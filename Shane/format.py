import string
import re
import sys


if len(sys.argv)< 2:
	print '\tstrip.py <inputfile.csv>'
	sys.exit(2)
f = open('formatted.csv','w')

exclude = set(string.punctuation)
exclude.remove('\'')
exclude.remove('?')
exclude.remove('#')
exclude.remove('-') 
exclude.remove('!')


for line in open(sys.argv[1], 'r'):
	line = line.lower()
	cols = line.split(',')
	diff = len(cols) -7
	newcols = [cols[0]] + [' '.join(cols[1:2+diff])]+ cols[2+diff:]

	for index in range(len(newcols)):
		colsans = ''
		for ch in newcols[index]:
			if ch not in exclude:
				colsans += ch
			else: 
				colsans += ' '
		newcols[index] = colsans 
		newcols[index] = newcols[index].replace('?',' ? ').replace('#',' # ').replace('!',' ! ').replace('\n','')
	# Rejoin and encapsulate in quotes for Predictions
	newline = ', '.join('"'+' '.join(newcols[i].split())+'"' for i in range(len(newcols)))
	newline += ', "' + str(len(newcols[1].split())) + '"'
	f.write(newline+'\n')
	