import csv
read = 10
out = csv.writer(open("myfile.csv","w"), delimiter=',',quoting=csv.QUOTE_ALL)
out.writerow(['value %d' % read])
out.writerow(['value %d' % read,'data'])
