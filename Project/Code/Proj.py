#!/usr/bin/env python2



# To DO:
# -Make Histogram
# -Use tempfiles
# -Make comments
# -Make it easier to run (argparse?) 

import sys
from Bio import SeqIO
from Bio.Seq import Seq
import pdb
import os
import glob
from subprocess import check_output
import dendropy
from dendropy.calculate import treecompare
import tempfile
import numpy as np


#For plotting stuff
import seaborn as sns 
sns.set(color_codes=True)
import matplotlib.pyplot as plt



def ReadFasta(filename):
	LetterList = []
	CompList = []
	VarList=[]
	Columns=[]
	Namelist=[]

									#Opens file and extracts each sequence as a list in a list
	with open(filename,'rU') as ih:
		for record in list(SeqIO.parse(ih, "fasta")):
			Namelist.append(record.id)			#Saves the name of each sequence in a list	
			for i in range(0, len(record.seq)):
				LetterList.append(record.seq[i]) 	#Letterlist extract the sequence and turns it in to a list
				
			CompList.append("".join(LetterList))		#Complist is a collection of all sequences
			LetterList = []	

									#Extracts each column for each sequence and saves in a list (Columns)
		for i in range(0, len(record.seq)):
			for m in range(len(CompList)):
				VarList.append(CompList[m][i])
			Columns.append("".join(VarList))
			VarList=[]
				
	return Columns, Namelist					#Columns is 1 element from each sequence saved as a list



def CompareColumns(Columns):
	''' Takes the three requirements for noise reduction and applies them to the Columns-list''' 						
	RemList = []
	ShortList = []
	count = {}
	New_ShortList = []
	

	for i in range(len(Columns)):
		RemList.append(''.join(set(Columns[i])))		#Creates a RemList that consist of only unique sequences of the Columns list, i.e. removes all aminoacids with multuple repeats.  

	
	for m in range(len(RemList)):					#Two If-statement makes sure that the number of unique sequences or indens does not exceed 50% of the column.  
		if float(len(RemList[m])) / len(Columns[m]) >= 0.5 or Columns[m].count('-')/float(len(Columns[m])) >= 0.5:
			ShortList.append(Columns[m].replace(Columns[m],len(Columns[m])*' ')) #If it exceeds 50%, it will be replaced with an empy column.
		else:							
			for s in Columns[m]:				#Goes through the column and check how many times every amino acid appears. 
				if count.has_key(s):
					count[s] += 1
				else:
					count[s] = 1
			for key in count:				#If any amino acid apperears more than twice, it appends in to ShortList which is the output if this function. 
				if count[key] > 2:
					ShortList.append(Columns[m])
					break 				#Breaks the check through that columns since at least one AA apperas more than twice. 
			count = {}

	return ShortList


def Printright(shortlist, Namelist, Columns):
	'''Changes lists to contain columns from original sequence to contain the sequence in a list. Both noise reduced (finlist) and non-reduced (Non_CleanList_Done).'''
	seqlist=[]
	donelist=[]
	finlist=[]
	Non_CleanList =[]						#Non_clean means that they havent been noise reduced, i.e. original sequence. 
	Non_CleanList_Done =[]
	for m in range(len(Namelist)):		
		for i in range(len(shortlist)):
			seqlist.append(shortlist[i][m]) 		#Changes the list from Columns (1 element from each sequence) to return each noise reduced sequence in a list. 
			Non_CleanList.append(Columns[i][m])		#Non-reduced columns are changed back to their sequence. 
		donelist.append("".join(seqlist))			#Noise reduced list with all sequences with spacing between each character. 
		Non_CleanList_Done.append("".join(Non_CleanList))	#Non-reduced with all sequences  
		Non_CleanList = []
		seqlist=[]
		finlist.append(donelist[m].replace(" ", ""))		#Final, noise reduced list with no spacing between each character. 
		
	return finlist, Non_CleanList_Done



def tred(counter, Namelist, finlist, Non_CleanList_Done):

	original=[]
	noise=[]
		
	'''Returns the symmetric difference between each noise and original alignment and the original tree.'''

	with open('fasta_orig', "w") as fo:  						#Creates a file with each alignment as a Fasta-format
		for n in range(len(Namelist)):	
			fo.write('\n' + '>' + Namelist[n] + '\n' + Non_CleanList_Done[n])

	with open('fasta_noise', 'w') as fn:
		for n in range(len(Namelist)):
			fn.write('\n' + '>' + Namelist[n] + '\n' + finlist[n])

	with open('fastprot_orig', 'w') as fpo: 					# Runs the command "fastprot" on file "fa_sekvens".  			
		fpo.write(check_output(["fastprot", 'fasta_orig']))
		
	with open('fastprot_noise', 'w') as fpn:
		fpn.write(check_output(["fastprot", 'fasta_noise']))	

	tempo=tempfile.TemporaryFile(mode='w+t')						# Creates a temporary file "temp" and makes it readable as text. Writes output of fnj to it.
	tempo.write(check_output(["fnj", "-O", "newick", "fastprot_orig"]))
	tempo.seek(0)
	
	tempn=tempfile.TemporaryFile(mode='w+t')						# Creates a temporary file "temp" and makes it readable as text. Writes output of fnj to it.
	tempn.write(check_output(["fnj", "-O", "newick", "fastprot_noise"]))
	tempn.seek(0)


	tns = dendropy.TaxonNamespace()
	t1 = dendropy.Tree.get(file=open(sys.argv[2], 'r'), schema="newick", tree_offset=0, taxon_namespace=tns)
	t2 = dendropy.Tree.get(file=tempo, schema="newick", tree_offset=0, taxon_namespace=tns)
	t3 = dendropy.Tree.get(file=tempn, schema="newick", tree_offset=0, taxon_namespace=tns)
	t1.encode_bipartitions()
	t2.encode_bipartitions()
	t3.encode_bipartitions()
	original=treecompare.symmetric_difference(t1, t2)				#Compares the symmetric difference between the two trees t1 and t2 
	noise=treecompare.symmetric_difference(t1, t3)
	tempo.close()
	tempn.close()
	

	return original, noise




def PlotHist(symdiff_original, symdiff_noise):

	plt.hist([symdiff_original, symdiff_noise], color=['r', 'b'], alpha=1, bins=25, label=["Original", "Noise Reduced"])
	plt.legend()
	plt.title(sys.argv[1])
	plt.xlabel('Symmetric Difference')
	plt.ylabel('Frequency')	
	plt.show()
	
		


def main():
	'''Main function that calls all the other functions'''
	longlist = []
	counter=0
	symdiff_original=[]
	symdiff_noise=[]
	for filename in glob.glob(os.path.join(sys.argv[1], '*.msl')): 		#Opens one file at a time with the .msl format in a selected folder typed as sys.argv[1]. 
		counter+=1
		#Remove stuff
		Columns, Namelist = ReadFasta(filename)
		shortlist = CompareColumns(Columns)
		longlist.append(shortlist)
		finlist, Non_CleanList_Done =Printright(shortlist, Namelist, Columns)
		original, noise = tred(counter, Namelist, finlist, Non_CleanList_Done)
		symdiff_original.append(original)
		symdiff_noise.append(noise)
		print(counter)

	with open('Stats_original.txt', "w") as ih: 
		ih.write("Mean = " + str(np.mean(symdiff_original)) + '\n' + "Median = " +  str(np.median(symdiff_original)) + '\n' + str(symdiff_original))
		
	with open('Stats_noise.txt', "w") as ih:
		ih.write("Mean = " + str(np.mean(symdiff_noise)) + '\n' + "Median = " +  str(np.median(symdiff_noise)) + '\n' + str(symdiff_noise)) #Creates a file with each alignment as a Fasta-format
		
		
	PlotHist(symdiff_original, symdiff_noise)

	

		


if __name__=='__main__':
	main()
