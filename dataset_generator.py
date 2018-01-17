#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
TITLE Synthetic Queries Generator
- input : generation rules & terms, external_dictionary file
- output : synthetic JSON dataset
LANGUAGE: Python 3.6 x64
AUTHOR: Sylvain Daronnat
YEAR: 2017
"""
import time
start_time=time.clock()
import re
import nltk
import copy
from datetime import datetime
from itertools import product
from collections import Counter
from num2words import num2words
from nltk import ngrams, word_tokenize
from collections import OrderedDict, defaultdict

###########################
# VARIABLES DECLARATIONS  #
###########################
# COUNTERS
cpt=0 # number of unique questions generated
cpt_dupli=0 # keep track of repetitions avoided in the output file
# DICTIONNARIES
tok_tag_dict={} # contain terms associated with equivalent terms
dict_entity={} # contains the associations of values and entities
gen_rules=defaultdict(list) # store the content of the generation rules file
possible_combinations=defaultdict(list) # contains the possible combinations of categories
meta_repertory=defaultdict(list) # contains meta categories names and their categories
meta_suf={} # contains meta suffixes
external_dictionary={} # contains fullnames of external_dictionary abreviations
# COUNTER
cnt_intents=Counter() # number of intents in the output file
# LISTS
list_kwd=[] # contains terms indicated as being "keywords"
# SET
query_set=set() # contain generated queries, safeguard against duplicates
# BOOLEAN
processing=False # indicate when the question generation has begun
def norma_res(a_string):
	"""
	Format numbers to words and abreviations to fullnames
	input = any string
	output = formatted string
	"""
	a_string=a_string.lower()
	new_str=""
	split_str=a_string.split(" ")
	for v in split_str:
		if v in external_dictionary: # we look into external_dictionary to see if the term already exists
			if new_str:
				new_str+=" "+external_dictionary[v]
			else:
				new_str=external_dictionary[v]
		else:
			if new_str:
				new_str+=" "+v
			else:
				new_str=v
	split_str=new_str.split(" ")
	final_str=""
	for v in split_str:
		if re.match("\d+",v):
			new_number=num2words(int(v)) # if the token is a number, we translate it
			if final_str:
				final_str+=" "+new_number
			else:
				final_str=new_number
		else:
			if final_str:
				final_str+=" "+v
			else:
				final_str=v
	final_str=final_str.replace(",", "")
	return final_str # return of the final string

############################################################################
# STEP 1/2 : PARSING THE GENERATION RESOURCES FILE
############################################################################
print("### STEP 1/2: Parsing of the generation file ###\n\tprocessing...")
rules_file_path='rules.txt'
rules_file=open(rules_file_path,'r',encoding='utf-8') # opening of the generation rules file
for cat in rules_file:
	if (re.search('^#',cat)): # we skip the comment lines
		pass
	elif(re.search('^\{META\}',cat)): # parsing of the meta categories (categories of categories)
		stripped_cat=cat.strip("{META}")
		get_meta_cat=stripped_cat.split("=")
		categories=get_meta_cat[1] # categories containg in the meta category
		meta_name_suf=get_meta_cat[0] # name of the meta category
		if(re.search("\|",meta_name_suf)):
			get_suf_meta=meta_name_suf.split("|")
			meta_name=get_suf_meta[0]
			suf_name=get_suf_meta[1] # isolation of suffixes, in order to delete them later
		else:
			meta_name=get_meta_cat[0]
			suf_name=""
		list_cat=categories.split(",")
		for catego in list_cat:
			meta_repertory[meta_name].append(catego.strip()) # append to a meta dict
			if suf_name:
				meta_suf[catego.strip()]=suf_name

	elif(re.search('^\[COMBINATORY\]',cat)): # parsing of the combinatorial rules
		get_intent_combi=cat.split("=")
		intent_combi=get_intent_combi[1]
		get_intent=intent_combi.split(":")
		intent_entity=get_intent[0].strip()
		if re.search("\|",intent_entity):
			get_entity=intent_entity.split("|") 
			intent=get_entity[0] # name of the intent associated with the query
			entity=get_entity[1] # same, but for the entity name
		else:
			intent=intent_entity
		combinatory=get_intent[1]
		every_combi=combinatory.split(";")
		for pos in every_combi:
			pos=pos.strip()
			if(re.search(",",pos)): # if there are multiple categories into one structure, we iterate over them
				get_each_cat=pos.split(",")
				for catego in get_each_cat:
					if catego in meta_repertory.keys(): # we check if a category is a meta category
						for val in meta_repertory[catego]:
							new_pos=pos.replace(catego,val)
							possible_combinations[intent].append(new_pos)
							if entity:
								dict_entity[new_pos]=entity
					elif pos not in possible_combinations[intent]: # else we add the combination as it was	
						possible_combinations[intent].append(pos)
						if entity:
							dict_entity[pos]=entity
			else: # else, we do the same for unique elements
				if pos in meta_repertory.keys():
					for val in meta_repertory[pos]:
						new_pos=pos.replace(pos,val)
						if entity:
							dict_entity[pos]=entity
							for v in meta_repertory[pos]:
								dict_entity[v]=entity
						possible_combinations[intent].append(new_pos)
				elif pos not in possible_combinations[intent]:
					possible_combinations[intent].append(pos)
					if entity:
						dict_entity[pos]=entity

	elif(re.search('=',cat)):
		is_a_keyword=False
		cat_struct=cat.split("=")
		if (re.search('\|keyword',cat_struct[0])): # we check if the parsed element is a keyword
			is_a_keyword=True # we set the boolean to "true"
			split_bar=cat_struct[0].split("|")
			cat=split_bar[0]
		else:
			cat=cat_struct[0]
		struct=cat_struct[1] # we store the corresponding structures for every category	
		if (re.search(',',struct)): # if the element has a "," then there is multiple equivalent for the same category
			list_struct=struct.split(",") # we isolate every element in the list of equivalent terms
			for elem in list_struct: # we append them to the list of multiple possibility for a category
				elem=elem.strip() # normalization
				elem=norma_res(elem)
				# print(elem)
				if elem:
					gen_rules[cat].append(elem)
				if is_a_keyword is True:
					list_kwd.append(elem)	
		else: # if a category has only one element, we simply store it in the corresponding dictionnary	
			struct=struct.strip()
			if is_a_keyword is True:
				list_kwd.append(struct)
			if struct:
				gen_rules[cat].append(struct)
rules_file.close() # we close the generation rules file
print("Done.")
############################################################################
# STEP 2/2 : GENERATION OF ALL THE POSSIBLE OUTPUT
############################################################################
print("\n### STEP 2/2: Generating output ###\n\tprocessing...")
print("\tFile used:",rules_file_path)
time_mark=datetime.now().strftime('%d-%m-%Y_%H-%M-%S') # time mark to identity output files
output_json=open('synth_dataset_'+time_mark+'.json','w',encoding='utf-8') # header of the synthetic jason dataset
output_json.write('{"rasa_nlu_data":\n\t{"common_examples":\n\t\t[')
aug_gen_rules=copy.deepcopy(gen_rules) # used to iterate over the first one and save new equivalent in the new, copied one
for intent_name in possible_combinations: # we read the keys of the combination dictionnary
	for struct in possible_combinations[intent_name]:
		# print("PARSING STRUCT:",struct)
		# print("\tTotal queries so far:",cpt)
		if struct in dict_entity:
			entity_name=dict_entity[struct]
		if (re.search(',',struct)): # we test if there is multiple structures for a combination
			list_struct=struct.split(",")
			cmd_product="product(" # initialization of the cartesian product command
			for elem in list_struct: # iteration over every structures
				for v in gen_rules[elem]:
					tok_tag_dict[v]=elem
				
				cmd_product+="aug_gen_rules['"+elem+"']," # increment the cartesian product command 
			cmd_product+=")" # end of the command
			eval_cmd=eval(cmd_product) # eval of the command as a python3 statement
			for elem in eval_cmd: # iteration over every generated combinations in the list
				synthetic_query="" # we initiate the variable that we will write as a final output
				lemma=""

				for term in elem: # for possible terms (may they be multiple or single)
					if term in list_kwd:
						term_to_find=copy.copy(term)
						if tok_tag_dict[term] in meta_suf:
							suf=meta_suf[tok_tag_dict[term]]
							lemma = tok_tag_dict[term]
							lemma = re.sub(meta_suf[tok_tag_dict[term]],"",lemma)
							lemma = re.sub("_"," ",lemma)
							lemma=lemma.lower()
						else:
							lemma=copy.copy(term.lower())
						if synthetic_query:
							synthetic_query+=" "+term
						else:
							synthetic_query+=term			
					else:
						if synthetic_query:
							synthetic_query+=" "+term
						else:
							synthetic_query+=term
				if synthetic_query not in query_set:
					query_set.add(synthetic_query)
					synthetic_query=synthetic_query.lower()
					start_idx=synthetic_query.index(term_to_find.lower())
					end_idx=start_idx+len(term_to_find)
					cnt_intents[intent_name]+=1 # adding to the counter of intents
					if processing is True:
						output_json.write(',')
					processing=True
					output_json.write('\n\t\t\t{"text": "'+synthetic_query+'", "intent": "'+intent_name+'", "entities": [{"start": '
						+str(start_idx)+', "end": '+str(end_idx)+', "value": "'+lemma+'", "entity": "'+entity_name+'"}')
					output_json.write(']}')
					cpt+=1 # increment the counter of unique queries
				else:
					cpt_dupli+=1
		# same treatement as above, but for structure with only one element, ex : "element|tag=one_struct" in the scenario
		# we assume that the end user will only ask about keyword/meaningful words	
		else:
			for elem in aug_gen_rules[struct]:
				synthetic_query=""
				if elem in list_kwd:
					term_to_find=copy.copy(elem)
					if elem in meta_suf:
						suf=meta_suf[elem]
						lemma = elem
						lemma = re.sub(meta_suf[elem],"",lemma)
						lemma = re.sub("_"," ",lemma)
						lemma=lemma.lower()
					else:
						lemma=copy.copy(elem.lower())
					if synthetic_query:
						synthetic_query+=" "+elem
					else:
						synthetic_query=elem
				if synthetic_query not in query_set:
					query_set.add(synthetic_query)
					synthetic_query=synthetic_query.lower()
					start_idx=synthetic_query.index(term_to_find.lower())
					end_idx=start_idx+len(term_to_find)
					if processing is True:
						output_json.write(',')
					processing=True
					output_json.write('\n\t\t\t{"text": "'+synthetic_query+'", "intent": "'+intent_name+'", "entities": [{"start": '
						+str(start_idx)+', "end": '+str(end_idx)+', "value": "'+lemma+'", "entity": "'+entity_name+'"}]}')
					cpt+=1
				else:
					cpt_dupli+=1

output_json.write("\n\t\t]\n\t}\n}") # we write the final information(s) to the output file
output_json.close() # we close the output file
print("Done.")
print("\n-> Number of unique queries generated:",cpt,"\n\t-> duplicates avoided:",cpt_dupli)
print("\nNumber of queries per Intents:")
print(cnt_intents)
end_time = time.clock() # calculate the runtime of the program and output it in the shell
final_time=end_time-start_time
if final_time > 60:
	time_mn=final_time/60
	print("\n Time elasped:",round(time_mn,3),"minutes(s)")
else:
	print("\n Time elasped:",round(final_time,3),"second(s)")
