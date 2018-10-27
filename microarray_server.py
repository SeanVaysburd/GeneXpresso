#!/usr/bin/python

import os.path, time
from os import listdir
from os.path import isfile, join
import json
import sys
from time import gmtime, strftime
import os
import socket
import uuid
from google.cloud import bigquery

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/genexpresso/.config\
/gcloud/genexpresso-bigquery.credentials.json"

dataset_name = "ancient-timing-169116.dna_microarray_study"
logFile = None

##################################################################################################

def get_db_connection():
    client = bigquery.Client()
    return client

##################################################################################################
def get_query_results(query):
    client = get_db_connection()
    results = []
    query_results = client.run_sync_query(query)
    query_results.use_legacy_sql = False
    query_results.run()
    page_token = None
    while True:
        rows, total_rows, page_token = query_results.fetch_data(
            max_results=1000,
            page_token=page_token)
        for row in rows:
            results.append(row)
        if not page_token:
            break
    return results

##################################################################################################

# datasets by keyword
#
# input format:
# jinp['keyword'] - search keyword
# jinp['search_in'] - column by which to search, one of: title, description, dataset_id, pubmed_id, gene, probe
# 
# output format:
# jout['status_code'] - 0 if correct, positive number otherwise
# jout['status_msg'] - 'OK' if correct, error message otherwise
# if status_code = 0, also includes:
# jout['result'] = list of { 'dataset_id': value, 'pubmed_id': value }

def datasets_by_keyword(jinp):
    response = None
    table_name = "`{}.genexpresso_dataset_descriptions`".format(dataset_name)
    pvalue_table_name = "`{}.genexpresso_pvalues`".format(dataset_name)

    try:
        mode = jinp['mode']
        keyword = jinp['keyword'].lower().strip()
        search_in = jinp['search_in']
        query = None
                    
        if search_in == 'title':
            query = ("SELECT dataset_ID, pubmed_ID FROM {} where lower({}) like '%{}%' order by dataset_ID".format(table_name, 'title', keyword))
        elif search_in == 'description':
            query = ("SELECT dataset_ID, pubmed_ID FROM {} where lower({}) like '%{}%' order by dataset_ID".format(table_name, 'description', keyword))
        elif search_in == 'dataset ID':
            query = ("SELECT dataset_ID, pubmed_ID FROM {} where lower({}) like '%{}%' order by dataset_ID".format(table_name, 'dataset_ID', keyword))
        elif search_in == 'pubmed ID':
            query = ("SELECT dataset_ID, pubmed_ID FROM {} where lower({}) like '%{}%' order by dataset_ID".format(table_name, 'pubmed_ID', keyword))
        elif search_in == 'gene':
            query = ("SELECT dataset_ID, pubmed_ID FROM {} where dataset_ID in (" \
                     "select distinct dataset_ID from {} where lower(gene) like '%{}%') order by dataset_ID".format(table_name, pvalue_table_name, keyword))
        elif search_in == 'probe':
            query = ("SELECT dataset_ID, pubmed_ID FROM {} where dataset_ID in (" \
                     "select distinct dataset_ID from {} where lower(probe) like '%{}%') order by dataset_ID".format(table_name, pvalue_table_name, keyword))
        else:
            raise Exception("Invalid search_in value")

        #logFile.write("query: {}\n".format(query))

        results = get_query_results(query)
        res = []
    
        for (dataset_ID, pubmed_ID) in results:
            res.append({"dataset_id": dataset_ID, "pubmed_id": str(pubmed_ID)})

        global logFile

        filename = save_file(res, 'datasets')
        response = {'status_code': '0', 'status_msg': 'OK', 'result': res, 'mode': mode, 'file': filename}

    except Exception as err:
        response = {'status_code': '1', 'status_msg': ('Error: ' + str(err))}
        #logFile.write("exception: {}".format(err))

    return json.dumps(response)

##################################################################################################

# pvalues by gene
#
# input format:
# jinp['gene'] - search gene name
# jinp['max_pvalue'] - max pvalue to return
# jinp['max_num_results'] - max # row to return
# jinp['min_sample_size'] - minimum sample size
#
# output format:
# jout['status_code'] - 0 if correct, positive number otherwise
# jout['status_msg'] - 'OK' if correct, error message otherwise
# if status_code = 0, also includes:
# list of { 'dataset_id': val, 'sample_1': val, 'sample_1_size': val, 'sample_2': val, 'sample_2_size': val, 'gene': val, 'probe': val, 'pvalue': val, 'tstat': val }
def pvalues_by_gene(jinp):
    response = None
    
    try:
        mode = jinp['mode']
        gene = jinp['gene'].lower().strip()
        max_pvalue = jinp['max_pvalue']
        max_num_results = jinp['max_num_results']
        min_sample_size = jinp['min_sample_size']
    
        query = ("select dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat from `{}.genexpresso_pvalues` " \
                " where lower(gene) like '%" + gene + \
                "%' and sample_size_1 >= " + min_sample_size + \
                " and sample_size_2 >= " + min_sample_size + \
                " and pvalue_x1e6 <= " + max_pvalue + \
                " * 1e6 order by pvalue_x1e6 limit " + max_num_results).format(dataset_name)

        results = get_query_results(query)
        res = []
    
        for (dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat) in results:
            res.append({"dataset_id": dataset_ID,
            'sample_1': sample_1,
            'sample_1_size': sample_size_1,
            'sample_2': sample_2,
            'sample_2_size': sample_size_2,
            'gene': gene,
            'probe': probe,
            'pvalue': "{:.10f}".format(pvalue_x1e6),
            'tstat': "{:.10f}".format(tstat) })

        filename = save_file(res, 'pvalues')
        response = {'status_code': '0', 'status_msg': 'OK', 'result': res, 'mode': mode, 'file': filename}    

    except Exception as err:
        response = {'status_code': '1', 'status_msg': ('Error: ' + str(err))}

    return json.dumps(response)

##################################################################################################

# pvalues by probe
#
# input format:
# jinp['probe'] - search probe name
# jinp['max_pvalue'] - max pvalue to return
# jinp['max_num_results'] - max # row to return
# jinp['min_sample_size'] - minimum sample size
#
# output format:
# jout['status_code'] - 0 if correct, positive number otherwise
# jout['status_msg'] - 'OK' if correct, error message otherwise
# if status_code = 0, also includes:
# list of { 'dataset_id': val, 'sample_1': val, 'sample_1_size': val, 'sample_2': val, 'sample_2_size': val, 'gene': val, 'probe': val, 'pvalue': val, 'tstat': val }
def pvalues_by_probe(jinp):
    response = None
    
    try:
        mode = jinp['mode']
        probe = jinp['probe'].lower().strip()
        max_pvalue = jinp['max_pvalue']
        max_num_results = jinp['max_num_results']
        min_sample_size = jinp['min_sample_size']
    
        query = ("select dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat from `{}.genexpresso_pvalues` " \
                " where lower(probe) like '%" + probe + \
                "%' and sample_size_1 >= " + min_sample_size + \
                " and sample_size_2 >= " + min_sample_size + \
                " and pvalue_x1e6 <= " + max_pvalue + \
                " * 1e6 order by pvalue_x1e6 limit " + max_num_results).format(dataset_name)

        results = get_query_results(query)
        res = []
    
        for (dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat) in results:
            res.append({"dataset_id": dataset_ID,
            'sample_1': sample_1,
            'sample_1_size': sample_size_1,
            'sample_2': sample_2,
            'sample_2_size': sample_size_2,
            'gene': gene,
            'probe': probe,
            'pvalue': "{:.10f}".format(pvalue_x1e6),
            'tstat': "{:.10f}".format(tstat) })

        filename = save_file(res, 'pvalues')
        response = {'status_code': '0', 'status_msg': 'OK', 'result': res, 'mode': mode, 'file': filename}    

    except Exception as err:
        response = {'status_code': '1', 'status_msg': ('Error: ' + str(err))}

    return json.dumps(response)

##################################################################################################

# pvalues for dataset
#
# input format:
# jinp['dataset_id'] - search dataset_id
# jinp['max_pvalue'] - max pvalue to return
# jinp['max_num_results'] - max # row to return
# jinp['min_sample_size'] - minimum sample size
#
# output format:
# jout['status_code'] - 0 if correct, positive number otherwise
# jout['status_msg'] - 'OK' if correct, error message otherwise
# if status_code = 0, also includes:
# list of { 'dataset_id': val, 'sample_1': val, 'sample_1_size': val, 'sample_2': val, 'sample_2_size': val, 'gene': val, 'probe': val, 'pvalue': val, 'tstat': val }
def pvalues_for_dataset(jinp):
    response = None
    
    try:
        mode = jinp['mode']
        dataset_id = jinp['dataset_id'].lower().strip()
        max_pvalue = jinp['max_pvalue']
        max_num_results = jinp['max_num_results']
        min_sample_size = jinp['min_sample_size']
        
        query = ("select dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat from `{}.genexpresso_pvalues` " \
                " where lower(dataset_ID) like '%" + dataset_id + \
                "%' and sample_size_1 >= " + min_sample_size + \
                " and sample_size_2 >= " + min_sample_size + \
                " and pvalue_x1e6 <= " + max_pvalue + \
                " * 1e6 order by pvalue_x1e6 limit " + max_num_results).format(dataset_name)
        #global logFile
        #logFile.write(query)

        results = get_query_results(query)
        res = []
        
        for (dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat) in results:
            res.append({"dataset_id": dataset_ID,
                        'sample_1': sample_1,
                        'sample_1_size': sample_size_1,
                        'sample_2': sample_2,
                        'sample_2_size': sample_size_2,
                        'gene': gene,
                        'probe': probe,
                        'pvalue': "{:.10f}".format(pvalue_x1e6),
                        'tstat': "{:.10f}".format(tstat) })
        
        filename = save_file(res, 'pvalues')
        response = {'status_code': '0', 'status_msg': 'OK', 'result': res, 'mode': mode, 'file': filename}    
        
    except Exception as err:
        response = {'status_code': '1', 'status_msg': ('Error: ' + str(err))}
       
    return json.dumps(response)

##################################################################################################

# title and description for a dataset
#
# input format:
# jinp['dataset_id'] - search dataset_id
#
# output format:
# jout['status_code'] - 0 if correct, positive number otherwise
# jout['status_msg'] - 'OK' if correct, error message otherwise
# if status_code = 0, also includes:
# { 'dataset_id': value, 'title': value, 'description': value }
def description_for_dataset(jinp):
    response = None
    
    try:
        mode = jinp['mode']
        dataset_id = jinp['dataset_id'].lower().strip()
        query = "select dataset_ID, title, description from `{}.genexpresso_dataset_descriptions`"\
                " where lower(dataset_ID) = lower('{}')".format(dataset_name, dataset_id)

        #logFile.write("query: {}\n".format(query))
        
        results = get_query_results(query)

        #logFile.write("results: {}\n".format(results))
        res = []
        
        for (dataset_ID, title, description) in results:
            res.append({"dataset_id": dataset_ID, "title": title, "description": description}) 
            
        response = {'status_code': '0', 'status_msg': 'OK', 'result': res, 'mode': mode}    
        
    except Exception as err:
        response = {'status_code': '1', 'status_msg': ('Error: ' + str(err))}
        #logFile.write("exception in description_for_dataset: {}\n".format(err))

    return json.dumps(response)

##################################################################################################

# subsets for a dataset
#
# input format:
# jinp['dataset_id'] - search dataset_id
#
# output format:
# jout['status_code'] - 0 if correct, positive number otherwise
# jout['status_msg'] - 'OK' if correct, error message otherwise
# if status_code = 0, also includes:
# list of { 'dataset_id': value, 'subset_name': value, 'subset_size': value }
def subsets_for_dataset(jinp):
    response = None
    
    try:
        mode = jinp['mode']
        dataset_id = jinp['dataset_id'].lower().strip()
        query = "select dataset_ID, subset_name, subset_size from `{}.genexpresso_dataset_subsets` " \
                "where lower(dataset_ID) = lower('{}') order by subset_size desc".format(dataset_name, dataset_id)
        
        results = get_query_results(query)
        res = []

        #logFile.write("query: {}\n".format(query))
        #logFile.write("results: {}\n".format(results))

        for (dataset_ID, subset_name, subset_size) in results:
            res.append({"dataset_id": dataset_ID, "subset_name": subset_name, "subset_size": subset_size}) 
        
        response = {'status_code': '0', 'status_msg': 'OK', 'result': res, 'mode': mode}    
        
    except Exception as err:
        response = {'status_code': '1', 'status_msg': ('Error: ' + str(err))}
        #logFile.write("exception: {}\n".format(err))

    return json.dumps(response)

##################################################################################################

def time_string():
    return strftime("%a, %d %b %Y %H:%M:%S", gmtime())

##################################################################################################

# pvalues for subsets
#
# input format:
# jinp['dataset_id'] - search dataset_id
# jinp['sample_1'] - sample #1
# jinp['sample_2'] - sample #2
# jinp['max_pvalue'] - max pvalue to return
# jinp['max_num_results'] - max # row to return
# jinp['min_sample_size'] - minimum sample size
#
# output format:
# jout['status_code'] - 0 if correct, positive number otherwise
# jout['status_msg'] - 'OK' if correct, error message otherwise
# if status_code = 0, also includes:
# list of { 'dataset_id': val, 'sample_1': val, 'sample_1_size': val, 'sample_2': val, 'sample_2_size': val, 'gene': val, 'probe': val, 'pvalue': val, 'tstat': val }
def pvalues_for_subsets(jinp):
    response = None
    
    try:
        mode = jinp['mode']
        dataset_id = jinp['dataset_id'].lower().strip()
        sample_1 = jinp['sample_1'].lower().strip().replace("'","''")
        sample_2 = jinp['sample_2'].lower().strip().replace("'","''")
        if (sample_1 == sample_2):
            raise Exception("sample_1 must be different from sample_2")
        
        max_pvalue = jinp['max_pvalue']
        max_num_results = jinp['max_num_results']
        min_sample_size = jinp['min_sample_size']
        
        query = ("select dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat from `{}.genexpresso_pvalues` " \
                " where lower(dataset_ID) like '%" + dataset_id + \
                "%' and lower(sample_1) = '" + sample_1 + "' and lower(sample_2) = '" + sample_2 + \
                "' and sample_size_1 >= " + min_sample_size + \
                " and sample_size_2 >= " + min_sample_size + \
                " and pvalue_x1e6 <= " + max_pvalue + \
                " * 1e6 order by pvalue_x1e6 limit " + max_num_results).format(dataset_name)
        #global logFile
        #logFile.write("\nSQL [" + time_string() + "] " + query + "\n")
        
        rows = get_query_results(query)
        #logFile.write("\nSQL [" + time_string() + "] " + str(len(rows)) + "\n")
        
        if len(rows) == 0:
            query = ("select dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat from `{}.genexpresso_pvalues` " \
                " where lower(dataset_ID) like '%" + dataset_id + \
                "%' and lower(sample_1) = '" + sample_2 + "' and lower(sample_2) = '" + sample_1 + \
                "' and sample_size_1 >= " + min_sample_size + \
                " and sample_size_2 >= " + min_sample_size + \
                " and pvalue_x1e6 <= " + max_pvalue + \
                " * 1e6 order by pvalue_x1e6 limit " + max_num_results).format(dataset_name)
            #global logFile
            #logFile.write("\nSQL [" + time_string() + "] " + query + "\n")
            rows = get_query_results(query)
            
        res = []
        
        for (dataset_ID, sample_1, sample_size_1, sample_2, sample_size_2, gene, probe, pvalue_x1e6, tstat) in rows:
            res.append({"dataset_id": dataset_ID,
                        'sample_1': sample_1,
                        'sample_1_size': sample_size_1,
                        'sample_2': sample_2,
                        'sample_2_size': sample_size_2,
                        'gene': gene,
                        'probe': probe,
                        'pvalue': "{:.10f}".format(pvalue_x1e6),
                        'tstat': "{:.10f}".format(tstat) })
        
        filename = save_file(res, 'pvalues')
        response = {'status_code': '0', 'status_msg': 'OK', 'result': res, 'mode': mode, 'file': filename}    
        
    except Exception as err:
        response = {'status_code': '1', 'status_msg': ('Error: ' + str(err))}
       
    return json.dumps(response)

##################################################################################################

def main():
    #inp = '{"gene": "TAGAP", "mode": "datasets_by_keyword", "keyword": "", "search_in": "title"}'
    #inp = '{"mode": "pvalues_by_gene", "gene": "FBXO42", "max_pvalue": "0.00001", "max_num_results": "100", "min_sample_size": "5"}'
    #inp = '{"mode": "pvalues_by_probe", "probe": "477", "max_pvalue": "0.00001", "max_num_results": "100", "min_sample_size": "5"}'
    #inp = '{"mode": "pvalues_for_dataset", "dataset_id": "GDS4425", "max_pvalue": "0.00001", "max_num_results": "10000", "min_sample_size": "5"}'
    #inp = '{"mode": "description_for_dataset", "dataset_id": "GDS4425"}'
    #inp = '{"mode": "subsets_for_dataset", "dataset_id1": "GDS4425"}'
    #inp = '{"mode": "pvalues_for_subsets", "dataset_id": "GDS4425", "sample_1": "CD4+ T-cells", "sample_2": "CD8+ T-cells", "max_pvalue": "0.01", "max_num_results": "10", "min_sample_size": "15"}'

    print "Content-type: application/json\n"    
    json_response = {"status_code": "0", "status_msg": "OK", "result": []}

    logFileName = "/var/log/genexpresso/access.log"
    global logFile
    logFile = open(logFileName, "a")
    origin = str(os.environ['REMOTE_ADDR']) + "," + str(socket.getfqdn(os.environ['REMOTE_ADDR']))
    
    # for testing only:
    #json_response = json.dumps({'status_code': '1', 'status_msg': 'Error: not yet implemented'})
    #print json_response
    #sys.exit(0)

    try:
        # for debugging, instead of reading inp from stdin, specify it directly
        inp = sys.stdin.read()
        jinp = json.loads(inp)
        mode = jinp['mode']

        if mode == 'datasets_by_keyword':
            json_response = datasets_by_keyword(jinp)
        elif mode == 'pvalues_by_gene':
            json_response = pvalues_by_gene(jinp)
        elif mode == 'pvalues_by_probe':
            json_response = pvalues_by_probe(jinp)
        elif mode == 'pvalues_for_dataset':
            json_response = pvalues_for_dataset(jinp)
        elif mode == 'description_for_dataset':
            json_response = description_for_dataset(jinp)
        elif mode == 'subsets_for_dataset':
            json_response = subsets_for_dataset(jinp)
        elif mode == 'pvalues_for_subsets':
            json_response = pvalues_for_subsets(jinp)
        else:
            raise Exception("Invalid mode: " + mode)

    except Exception as err:
        json_response = json.dumps({'status_code': '1', 'status_msg': ('Error: ' + str(err))}) 

    print json_response

    logFile.write("IN [" + str(origin) + ":" + time_string() + "] " + inp + "\n")

    #logFile.write("\nIN [" + time_string() + "] " + inp + "\n")
    #logFile.write("\nOUT [" + str(origin) + ":" + time_string() + "] " + json_response + "\n")

##################################################################################################

def save_file(res, prefix):
    global logFile

    # delete old files after 1 day
    expiration_seconds = 12 * 3600
    www_dir = '/var/www/html/';
    results_dir = 'query_results/';
    results_path = join(www_dir, results_dir)
    files = listdir(results_path)
    now = time.time()
    for f in files:
        file_path = join(results_path, f)
        if isfile(file_path) and file_path.endswith('.csv'):
            mod_time = os.path.getmtime(file_path)
            elapsed_seconds = now - mod_time
            if (elapsed_seconds > expiration_seconds):
                os.remove(file_path)

    filename = 'query_results/' + prefix + '.' + str(len(res)) + '.' + str(uuid.uuid4()) + ".csv"

    #logFile.write("WRITE " + filename + "\n")

    fh = open(www_dir + filename, 'w')
    keys = None

    for line in res:
        if keys == None:
            keys = list(line.keys())
            keys.sort()
            fh.write(','.join(keys) + "\n")
        
        values = [str(line[x]) for x in keys]
        fh.write(','.join(values) + "\n")
        
    fh.close()

    #logFile.write("WRITE " + filename + "\n")

    return filename

##################################################################################################

main()

##################################################################################################
