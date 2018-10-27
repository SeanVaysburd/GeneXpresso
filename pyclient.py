import json
#import requests
from browser import alert
from browser import document
#import Image
import sys
from browser import ajax
#alert("Pi: ")
from browser.session_storage import storage as session_storage
from browser import html
import browser.svg as svg

buttonHome = None
buttonAbout = None
buttonGuide = None
buttonContact = None
buttonSendEmail = None
bSearch1 = None
bSearch2 = None
bSearch3 = None
bSearch4 = None
dataset = None

numOpenRequests = 0

#######################################################################################
#inp = '{"gene": "TAGAP", "mode": "datasets_by_keyword", "keyword": "", "search_in": "title"}'
    #inp = '{"mode": "pvalues_by_gene", "gene": "FBXO42", "max_pvalue": "0.00001", "max_num_results": "100", "min_sample_size": "5"}'
    #inp = '{"mode": "pvalues_by_probe", "probe": "477", "max_pvalue": "0.00001", "max_num_results": "100", "min_sample_size": "5"}'
    #inp = '{"mode": "pvalues_for_dataset", "dataset_id": "GDS4425", "max_pvalue": "0.00001", "max_num_results": "10000", "min_sample_size": "5"}'
    #inp = '{"mode": "description_for_dataset", "dataset_id": "GDS4425"}'
    #inp = '{"mode": "subsets_for_dataset", "dataset_id1": "GDS4425"}'
    #inp = '{"mode": "pvalues_for_subsets", "dataset_id": "GDS4425", "sample_1": "CD4+ T-cells", "sample_2": "CD8+ T-cells", "max_pvalue": "0.01", "max_num_results": "10", "min_sample_size": "15"}'
    
def onComplete(req):
    status_indicator_ready(1)
    try:
        #document <= html.BR()
        #document <= "received response with status "
        #document <= req.status
        #document <= html.BR()
    
        if req.status != 200 and req.status != 0:
            #document <= "HTTP response error: " + str(req.status)
            return

        jres = json.loads(req.text)
        status_code = jres['status_code']
        status_msg = jres['status_msg']

        if (status_code != "0"):
            #document <= "Error status code: " + status_code + ", status msg: " + status_msg
            return
        
        mode = jres['mode']
        res = jres['result']

        #session_storage['last_answer'] = str(res)
        #document <= ("response: mode " + mode + ", result " + str(res))
        #document <= html.BR()

        if mode == 'datasets_by_keyword':
            output_file = jres['file']
            setup_dataset_list_table(res, output_file)
        elif mode == 'pvalues_by_gene':
            output_file = jres['file']
            setup_pvalue_list_table(res, output_file)
        elif mode == 'pvalues_by_probe':
            output_file = jres['file']
            setup_pvalue_list_table(res, output_file)
        elif mode == 'pvalues_for_dataset':
            output_file = jres['file']
            setup_pvalue_list_table(res, output_file)
        elif mode == 'description_for_dataset':
            setup_dataset_description(res)
        elif mode == 'subsets_for_dataset':
            setup_samples_to_search(res)
        elif mode == 'pvalues_for_subsets':
            output_file = jres['file']
            setup_pvalue_list_table(res, output_file)
        #else:
            #document <= ("invalid mode: " + mode)
            #document <= html.BR()
 
    except Exception as err:
        #document <= "Error processing response: " + str(err)
        return
    
    
#######################################################################################

def setup_samples_to_search(res):
    sample_1 = document["selector_samples_1"]
    sample_2 = document["selector_samples_2"]
    sample_1.options.length = 0
    sample_2.options.length = 0
    for each in res:
        sample_1.add(html.OPTION(each["subset_name"]))
        sample_2.add(html.OPTION(each["subset_name"]))

#######################################################################################

def setup_dataset_description(res):
    global dataset
    record = res[0]
    datasetId = record["dataset_id"]
    dataset = datasetId
    title = record["title"]
    description = record["description"]

    label_details_for_dataset = document["label_details_for_dataset"]
    text_area_description = document["dataset_description"]
    text_area_title = document["dataset_title"]

    label_details_for_dataset.text = "Details for dataset " + datasetId + ":"
    text_area_description.value = "Description: " + description
    text_area_title.value = "Title: " + title
    
#######################################################################################

# this has to be global to keep track of direction of the latest preceding sort.
# each time the table is sorted by a column, the direction is flipped from the latest preceding time. 
orders = {}

def sort_by_col(evt, title, rows, tableBody, numeric):
    
    #document <= html.BR() + "num rows: " + str(len(rows))

    cell = evt.target
    
    # get title cell
    th_elt = cell.closest('TH')

    # get column of title cell
    for i, th in enumerate(title.children):
        if th == th_elt:
            col_num = i
            #document <= html.BR() + "col_num = " + str(col_num) + ", numeric: " + str(numeric)
            break

    # up / down flag is flipped from the previous setting. this is why orders = {} has to be global.
    if col_num not in orders:
        if numeric:
            orders[col_num] = 'down'
        else:
            orders[col_num] = 'up'
    elif orders[col_num] == 'up':
        orders[col_num] = 'down'
    else:
        orders[col_num] = 'up'
        
    ascending = orders[col_num]

    #document <= html.BR() + "col_num = " + str(col_num) + ", numeric: " + str(numeric) + ", ascending: " + ascending

    # sort rows based on the text in cells in the specified column
    def k_str(_item):
        return _item.children[col_num].text

    # sort rows based on the numeric value in cells in the specified column
    def k_num(_item):
        return float(_item.children[col_num].text)

    if not numeric:
        func = k_str
    else:
        func = k_num

    rows.sort(key = func)

    if ascending == 'down':
        rows.reverse()

    tableBody <= rows

#######################################################################################

def button_style_default(b):
    b.style.background = "#DDDDDD"
    b.style.color = "#505050"
    b.style.border = "none"
    b.style.fontSize = "large"   
    b.style.marginLeft = "50px"
    #b.style.marginTop = "30px"
    b.style.verticalAlign = "top"
    b.style.padding = "10px 30px"
    b.style.border = "thin solid gray"

#######################################################################################

def button_style_hover(b):
    b.style.background = "#BBBBBB"
    b.style.color = "#202020"
    b.style.border = "thin solid gray"

##############################################################
    
def mouse_over_search1(ev):
    global bSearch1
    button_style_hover(bSearch1)

def mouse_out_search1(ev):
    global bSearch1
    button_style_default(bSearch1)

##############################################################

def click_search2(ev):
    select_probe_or_gene = document["select_probe_or_gene"]
    input_probe_or_gene = document["input_probe_or_gene"]
    selector_min_sample_size = document["selector_min_sample_size"]
    selector_max_pvalue = document["selector_max_pvalue"]
    selector_max_num_results = document["selector_max_num_results"]
    
    req = ajax.ajax()
    req.bind('complete', onComplete)
    req.open('POST', "cgi-bin/microarray_server.py", True)
    req.set_header('content-type', 'application/json')

    if select_probe_or_gene.value == "gene name":
        req.send(json.dumps({'mode': "pvalues_by_gene",
                             'gene': input_probe_or_gene.value,
                             'max_pvalue': selector_max_pvalue.value,
                             'max_num_results': selector_max_num_results.value,
                             'min_sample_size': selector_min_sample_size.value}))
        status_indicator_computing(1)
        
    elif select_probe_or_gene.value == "probe name":
        req.send(json.dumps({'mode': "pvalues_by_probe",
                             'probe': input_probe_or_gene.value,
                             'max_pvalue': selector_max_pvalue.value,
                             'max_num_results': selector_max_num_results.value,
                             'min_sample_size': selector_min_sample_size.value}))
        status_indicator_computing(1)
        
def mouse_over_search2(ev):
    global bSearch2
    button_style_hover(bSearch2)

def mouse_out_search2(ev):
    global bSearch2
    button_style_default(bSearch2)

##############################################################

def click_search3(ev):
    x = 1
    
def mouse_over_search3(ev):
    global bSearch3
    button_style_hover(bSearch3)

def mouse_out_search3(ev):
    global bSearch3
    button_style_default(bSearch3)

##############################################################

def click_search4(ev):
    x = 1
    
def mouse_over_search4(ev):
    global bSearch4
    button_style_hover(bSearch4)

def mouse_out_search4(ev):
    global bSearch4
    button_style_default(bSearch4)
    
##############################################################

def click_search_subsets(ev):
    sample_1 = document["selector_samples_1"].value
    sample_2 = document["selector_samples_2"].value 
    global dataset
    selector_min_sample_size = document["selector_min_sample_size"]
    selector_max_pvalue = document["selector_max_pvalue"]
    selector_max_num_results = document["selector_max_num_results"]
    
    req = ajax.ajax()
    req.bind('complete', onComplete)
    req.open('POST', "cgi-bin/microarray_server.py", True)
    req.set_header('content-type', 'application/json')
    req.send(json.dumps({'mode': 'pvalues_for_subsets', 'dataset_id': dataset, 'sample_1': sample_1,
                             'sample_2': sample_2,
                             'max_pvalue': str(selector_max_pvalue.value),
                             'max_num_results': str(selector_max_num_results.value),
                             'min_sample_size': str(selector_min_sample_size.value)}))
    status_indicator_computing(1)
def mouse_over_search_subsets(ev):
    b = ev.target
    button_style_hover(b)

def mouse_out_search_subsets(ev):
    b = ev.target
    button_style_default(b)
    
##############################################################

def click_home(ev):
    #document <= html.BR()
    #document <= "home"
    clear_main_panel()
    draw_home()
    
def mouse_over_home(ev):
    global buttonHome
    button_style_hover(buttonHome)

def mouse_out_home(ev):
    global buttonHome
    button_style_default(buttonHome)

##############################################################

def click_about(ev):
    #document <= html.BR()
    #document <= "about"
    clear_main_panel()
    draw_about()
    
def mouse_over_about(ev):
    global buttonAbout
    button_style_hover(buttonAbout)

def mouse_out_about(ev):
    global buttonAbout
    button_style_default(buttonAbout)

##############################################################

def click_guide(ev):
    #document <= html.BR()
    #document <= "guide"
    clear_main_panel()
    draw_guide()
    
def mouse_over_guide(ev):
    global buttonGuide
    button_style_hover(buttonGuide)

def mouse_out_guide(ev):
    global buttonGuide
    button_style_default(buttonGuide)

##############################################################

def click_contact(ev):
    #document <= html.BR()
    #document <= "contact"
    clear_main_panel()
    draw_contact()
    
def mouse_over_contact(ev):
    global buttonContact
    button_style_hover(buttonContact)

def mouse_out_contact(ev):
    global buttonContact
    button_style_default(buttonContact)

##############################################################

def click_dataset_id_button(ev):
    b = ev.target
    datasetID = b.gds
    min_sample_size = document["selector_min_sample_size"]
    max_pvalue = document["selector_max_pvalue"]
    max_num_results = document["selector_max_num_results"]
    min_sample_size = min_sample_size.value
    max_pvalue = max_pvalue.value
    max_num_results = max_num_results.value

    req = ajax.ajax()
    req.bind('complete', onComplete)
    req.open('POST', "cgi-bin/microarray_server.py", True)
    req.set_header('content-type', 'application/json')
    req.send(json.dumps({'mode': 'description_for_dataset', 'dataset_id': datasetID}))

    teq = ajax.ajax()
    teq.bind('complete', onComplete)
    teq.open('POST', "cgi-bin/microarray_server.py", True)
    teq.set_header('content-type', 'application/json')
    teq.send(json.dumps({'mode': 'subsets_for_dataset', 'dataset_id': datasetID}))

    leq = ajax.ajax()
    leq.bind('complete', onComplete)
    leq.open('POST', "cgi-bin/microarray_server.py", True)
    leq.set_header('content-type', 'application/json')
    leq.send(json.dumps({'mode': 'pvalues_for_dataset', 'dataset_id': datasetID, 'min_sample_size': str(min_sample_size), 'max_pvalue': str(max_pvalue), 'max_num_results': str(max_num_results)}))

    status_indicator_computing(3)
    
def mouse_over_button(ev):
    b = ev.target
    b.style.background = "#BBBBBB"

def mouse_out_button(ev):
    b = ev.target
    b.style.background = "#EEEEEE"
        
##############################################################

def mouse_over_send_email(ev):
    global buttonSendEmail
    button_style_hover(buttonSendEmail)

def mouse_out_send_email(ev):
    global buttonSendEmail
    button_style_default(buttonSendEmail)
    
##############################################################

def clear_main_panel():
    panel = document["main_panel"]
    for c in panel.children:
        panel.remove(c)
##############################################################

def datasets_by_keyword_search(ev):
    panel = document["main_panel"]
    #document <= panel
    #panel.getValues()
    #root = panel.element.dom
    #x = panel.g12.value
    #keyword = panel.getAttribute("g12")
    #keyword = panel["g12"].value
    #search_in = panel.getAttribute("sel1")
    #search_in = panel["sel1"].value
    #g12 = document["g12"]

    keyword = document["g12"].value
    search_in = document["selector1"].value

    #keyword = g12.value
    #search_in = sel1.value

    #document <= keyword
    #document <= search_in

    req = ajax.ajax()
    req.bind('complete', onComplete)
    req.open('POST', "cgi-bin/microarray_server.py", True)
    req.set_header('content-type', 'application/json')
    #req.set_header('Access-Control-Allow-Origin', '*')
    req.send(json.dumps({'mode': 'datasets_by_keyword', 'keyword': keyword, 'search_in': search_in}))

    status_indicator_computing(1)
    
##############################################################

def status_indicator_ready(numCompleted):
    global numOpenRequests
    numOpenRequests = numOpenRequests - numCompleted
    #document <= "status_indicator_ready: numOpenRequests = " + str(numOpenRequests)
    
    if (numOpenRequests <= 0):
        b = document["status_indicator"]
        b.text = "READY"
        b.style.verticalAlign = "bottom"
        b.style.marginRight = "40px"
        b.style.background = "#55FF55"
        b.style.color = "#000000"
        b.style.width = "120px"
        b.style.textAlign = "center"
        b.style.padding = "10px 0px 10px 0px"
        b.style.font = "16px verdana"
        b.style.border = "thin solid green"

def status_indicator_computing(numNewRequests):
    global numOpenRequests
    numOpenRequests = numOpenRequests + numNewRequests
    #document <= "status_indicator_computing: numOpenRequests = " + str(numOpenRequests)
    b = document["status_indicator"]
    b.text = "COMPUTING"
    b.style.verticalAlign = "bottom"
    b.style.marginRight = "40px"
    b.style.background = "#3366FF"
    b.style.color = "#FFEE00"
    b.style.width = "120px"
    b.style.textAlign = "center"
    b.style.padding = "10px 0px 10px 0px"
    b.style.font = "16px verdana"
    b.style.border = "thin solid blue"

##############################################################

def draw_home1():
    panel = document["main_panel"]
    table0 = html.TABLE()
    tableBody0 = html.TBODY()
    row0 = html.TR()
    
    b21 = html.P(id = "status_indicator")
    
    #b21.text = "READY"
    #b21.style.verticalAlign = "bottom"
    #b21.style.marginRight = "40px"
    #g21.style.background = "#3366FF"
    #g21.style.color = "#FFEE00"
    #b21.style.background = "#55FF55"
    #b21.style.width = "120px"
    #b21.style.textAlign = "center"
    #b21.style.padding = "10px 0px 10px 0px"
    #b21.style.font = "16px verdana"
    #b21.style.border = "thin solid green"

    td01 = html.TD()
    td01 <= b21
    row0 <= td01
    
    head = html.LABEL("GeneXpresso - analyze DNA microarray datasets")
    head.style.font = "30px verdana"
    head.style.textAlign = "center"
    td02 = html.TD()
    td02 <= head
    row0 <= td02

    tableBody0 <= row0
    table0 <= tableBody0
    panel <= table0

    panel <= html.BR()
    
    status_indicator_ready(0)
    
    table1 = html.TABLE()
    table1.style.border = "none"
    table1.style.fontSize = "large"
    table1.style.background = "#F7F7F7"
    #table1.style.marginLeft = "50px"
    #b.style.marginTop = "30px"
    #
    table1.style.padding = "10px 20px 10px 10px"
    table1.style.font = "16px verdana"
    
    tableBody1 = html.TBODY()
    
    g1 = html.TR()
    
    g11 = html.LABEL("Search datasets by keyword:")
    g11.style.verticalAlign = "bottom"
    g11.style.marginRight = "10px"

    td_1 = html.TD()
    td_1 <= g11
    g1 <= td_1

    g12 = html.INPUT(id="g12")
    g12.style.verticalAlign = "bottom"
    g12.style.marginRight = "20px"

    td_2 = html.TD()
    td_2 <= g12
    g1 <= td_2

    g13 = html.LABEL("Search in:")
    g13.style.verticalAlign = "bottom"
    g13.style.marginRight = "10px"

    td_3 = html.TD()
    td_3 <= g13
    g1 <= td_3

    op1 = html.OPTION("title")
    op2 = html.OPTION("description")
    op3 = html.OPTION("dataset ID")
    op4 = html.OPTION("pubmed ID")
    op5 = html.OPTION("gene")
    op6 = html.OPTION("probe")
    sel1 = html.SELECT([op1, op2, op3, op4, op5, op6], id="selector1", font_size=12)
    sel1.style.fontSize = "large"
    sel1.style.verticalAlign = "bottom"

    td_4 = html.TD()
    td_4 <= sel1
    g1 <= td_4
    
    global bSearch1
    bSearch1 = html.BUTTON('Search')
    button_style_default(bSearch1)
    #bSearch1.bind('click', click_search1)
    bSearch1.bind('mouseout', mouse_out_search1)
    bSearch1.bind('mouseover', mouse_over_search1)
    bSearch1.style.verticalAlign = "top"
    bSearch1.bind('click', datasets_by_keyword_search)

    td_5 = html.TD()
    td_5 <= bSearch1
    g1 <= td_5

    tableBody1 <= g1
    table1 <= tableBody1
    panel <= table1
    panel <= html.BR()

##############################################################

def draw_home2():
    panel = document["main_panel"]
    
    table21 = html.TABLE()
    table21.style.fontSize = "large"
    table21.style.font = "16px verdana"
    
    tableBody21 = html.TBODY()

    #table22 = html.TABLE()
    #tableBody22 = html.TBODY()
    
    row21_1 = html.TR()
    #row21_2 = html.TR()

    table21.style.background = "#F7F7F7"
    table21.style.padding = "10px 25px 10px 10px"

    #table22.style.background = "#F7F7F7"
    #table22.style.padding = "10px 15px 10px 10px"
    
    label21 = html.LABEL("Search gene expressions by:")
    label21.style.verticalAlign = "center"
    label21.style.marginRight = "10px"

    td_1 = html.TD()
    td_1 <= label21
    row21_1 <= td_1

    op1 = html.OPTION("probe name")
    op2 = html.OPTION("gene name")
    sel2 = html.SELECT([op2, op1], id="select_probe_or_gene", font_size=16)
    sel2.style.fontSize = "large"
    sel2.style.verticalAlign = "center"
    sel2.style.marginRight = "20px"

    td_2 = html.TD()
    td_2 <= sel2
    row21_1 <= td_2

    inp21 = html.INPUT(id="input_probe_or_gene")
    inp21.style.verticalAlign = "center"
    inp21.style.marginRight = "0px"

    td_3 = html.TD()
    td_3 <= inp21
    row21_1 <= td_3

    global bSearch2
    bSearch2 = html.BUTTON('Search')
    button_style_default(bSearch2)
    bSearch2.bind('click', click_search2)
    bSearch2.bind('mouseout', mouse_out_search2)
    bSearch2.bind('mouseover', mouse_over_search2)
    bSearch2.style.verticalAlign = "center"

    td_4 = html.TD()
    td_4 <= bSearch2
    row21_1 <= td_4
    
    #label22 = html.LABEL("Search gene expressions by gene name:")
    #label22.style.verticalAlign = "bottom"
    #label22.style.marginRight = "10px"
    #row21_2 <= label22
    #inp22 = html.INPUT()
    #inp22.style.verticalAlign = "bottom"
    #inp22.style.marginRight = "0px"
    #row21_2 <= inp22
    #global bSearch3
    #bSearch3 = html.BUTTON('Search')
    #button_style_default(bSearch3)
    #bSearch3.bind('click', click_search3)
    #bSearch3.bind('mouseout', mouse_out_search3)
    #bSearch3.bind('mouseover', mouse_over_search3)
    #bSearch3.style.verticalAlign = "top"
    #row21_2 <= bSearch3
    
    tableBody21 <= row21_1
    #tableBody22 <= row21_2
    table21 <= tableBody21
    #table22 <= tableBody22

    panel <= table21
    panel <= html.BR()
    #panel <= table22
     
    #############################################
    
    table23 = html.TABLE()
    table23.style.font = "16px verdana"
    table23.style.background = "#F7F7F7"
    table23.style.padding = "20px 25px 20px 10px"
    
    tableBody23 = html.TBODY()

    row23_1 = html.TR()
    row23_2 = html.TR()
    row23_3 = html.TR()

    label23_1 = html.LABEL("Min sample size:")
    #label23_1.style.verticalAlign = "bottom"
    label23_1.style.marginRight = "10px"
    row23_1 <= label23_1

    op21 = html.OPTION("5")
    op22 = html.OPTION("10")
    op23 = html.OPTION("15")
    op24 = html.OPTION("20")
    op25 = html.OPTION("25")
    sel23_1 = html.SELECT([op21, op22, op23, op24, op25], id="selector_min_sample_size", font_size=16)
    sel23_1.style.fontSize = "large"
    #sel23_1.style.verticalAlign = "bottom"
    sel23_1.style.marginRight = "50px"
    row23_1 <= sel23_1
    
    #inp23_1 = html.INPUT()
    #inp23_1.style.verticalAlign = "bottom"
    #inp23_1.style.marginRight = "0px"
    #row23_1 <= inp23_1

    label23_2 = html.LABEL("Max p-value:")
    label23_2.style.verticalAlign = "bottom"
    label23_2.style.marginRight = "10px"
    row23_1 <= label23_2

    op31 = html.OPTION("1E-6")
    op32 = html.OPTION("1E-5")
    op33 = html.OPTION("1E-4")
    op34 = html.OPTION("1E-3")
    op35 = html.OPTION("0.005")
    op36 = html.OPTION("0.01")
    op37 = html.OPTION("0.02")
    op38 = html.OPTION("0.05")
    sel23_2 = html.SELECT([op38, op37, op36, op35, op34, op33, op32, op31], id="selector_max_pvalue", font_size=16)
    sel23_2.style.fontSize = "large"
    #sel23_1.style.verticalAlign = "bottom"
    sel23_2.style.marginRight = "50px"
    row23_1 <= sel23_2
    
    #inp23_2 = html.INPUT()
    #inp23_2.style.verticalAlign = "bottom"
    #inp23_2.style.marginRight = "0px"
    #row23_1 <= inp23_2
    
    label23_3 = html.LABEL("Max # results:")
    label23_3.style.verticalAlign = "bottom"
    label23_3.style.marginRight = "10px"
    row23_1 <= label23_3

    op44 = html.OPTION("1000")
    op45 = html.OPTION("500")
    op46 = html.OPTION("300")
    op47 = html.OPTION("200")
    op48 = html.OPTION("100")
    sel23_3 = html.SELECT([op48, op47, op46, op45, op44], id="selector_max_num_results", font_size=16)
    sel23_3.style.fontSize = "large"
    #sel23_3.style.verticalAlign = "bottom"
    sel23_3.style.marginRight = "0px"
    row23_1 <= sel23_3
    
    #inp23_3 = html.INPUT()
    #inp23_3.style.verticalAlign = "bottom"
    #inp23_3.style.marginRight = "0px"
    #row23_1 <= inp23_3

    tableBody23 <= row23_1
    #tableBody23 <= row23_2
    #tableBody23 <= row23_3

    table23 <= tableBody23
    panel <= table23
    
    panel <= html.BR()

##############################################################

#
# dataPairs is a list of {'dataset_id': 'GDS1478', 'pubmed_id': '16351713'} dictionaries
#
def setup_dataset_list_table(dataPairs, output_file):
    aLeft = document["aLeft"]
    aLeft.href = output_file

    table = document["dataset_list_table"]

    for child in table:
        table.remove(child)
                
    tableBody = html.TBODY()
    headers = html.TR()
    tableBody.style.border = "thin solid lightgray"

    # to clear list, do this:    del left_table_rows [:]
    dataset_list_table_rows = []
    
    link = html.A('\u2191\u2193', href="#", Class="sort_link")
    link.bind('click',lambda ev:sort_by_col(ev,headers,dataset_list_table_rows,tableBody,False))
    
    link_num = html.A('\u2191\u2193', href="#", Class="sort_link")
    link_num.bind('click',lambda ev:sort_by_col(ev,headers,dataset_list_table_rows,tableBody,True))

    hD = html.TH('Dataset ID' + link)
    hP = html.TH('PubMed ID' + link.clone())
    
    hList = [hD, hP]

    for h in hList:
        h.style.background = "#E0E0E0"
        h.style.font = "16px verdana"
        
    h = None
    headers <= hList

    for i in range(len(dataPairs)):
        pair = dataPairs[i]
        datasetId = pair['dataset_id']
        pubmedId = pair['pubmed_id']
                        
        row = html.TR()

        button = html.BUTTON(datasetId, gds = datasetId)
        button.style.font = "16px verdana"
        button.value = datasetId
        button.bind('mouseout', mouse_out_button)
        button.bind('mouseover', mouse_over_button)
        button.bind('click', click_dataset_id_button)
        button.style.border = "thin solid gray"
        button.style.background = "#EEEEEE"
        button.style.color = "#505050"
    
        td1 = html.TD(button)
        td1.style.textAlign = "center"
        button.style.width = "100px"
        
        td2 = html.TD(html.A(pubmedId, href="http://www.ncbi.nlm.nih.gov/pubmed/?term=" + pubmedId, target="_blank"))
        td2.style.textAlign = "center"

        tdList = [td1, td2]

        if (i % 2 == 1):
            for td in tdList:
                td.style.background = "#F7F7F7"
        
        row <= tdList
        dataset_list_table_rows.append(row)
    
    tableBody <= headers
    tableBody <= dataset_list_table_rows
    table <= tableBody

##############################################################
#
# dataPairs is a list of {"tstat": "-21.2255485000", "probe": "33760_at", "sample_2_size": 20, "sample_1_size": 20,
# "dataset_id": "GDS4425", "gene": "PEX14", "sample_2": "CD8+ T-cells", "sample_1": "CD4+ T-cells", "pvalue": "0.0000000000"}
#
def setup_pvalue_list_table(dataPairs, output_file):
    aRight = document["aRight"]
    aRight.href = output_file

    pvaluesTable = document["pvalue_list_table"]

    for child in pvaluesTable:
        pvaluesTable.remove(child)
        
    pvaluesTableBody = html.TBODY()
    pvaluesTableHeaders = html.TR()
    pvaluesTableBody.style.border = "thin solid lightgray"

    # to clear list, do this:    del left_table_rows [:]
    pvaluesTableRows = []
    
    pvaluesLink = html.A('\u2191\u2193', href="#", Class="sort_link")
    pvaluesLink.bind('click',lambda ev:sort_by_col(ev,pvaluesTableHeaders,pvaluesTableRows,pvaluesTableBody,False))
    
    pvaluesLinkNum = html.A('\u2191\u2193', href="#", Class="sort_link")
    pvaluesLinkNum.bind('click',lambda ev:sort_by_col(ev,pvaluesTableHeaders,pvaluesTableRows,pvaluesTableBody,True))

    h1 = html.TH('Dataset ID' + pvaluesLink)
    h2 = html.TH('Sample1' + pvaluesLink.clone())
    h3 = html.TH('Size1' + pvaluesLinkNum)
    h4 = html.TH('Sample2' + pvaluesLink.clone())
    h5 = html.TH('Size2' + pvaluesLinkNum.clone())
    h6 = html.TH('Gene' + pvaluesLink.clone())
    h7 = html.TH('Probe' + pvaluesLink.clone())
    h8 = html.TH('P-value x1E6' + pvaluesLinkNum.clone())
    h9 = html.TH('T-stat' + pvaluesLinkNum.clone())
                             
    pvaluesHeadersList = [h1, h2, h3, h4, h5, h6, h7, h8, h9]

    for h in pvaluesHeadersList:
        h.style.background = "#E0E0E0"
        h.style.font = "16px verdana"
        
    pvaluesTableHeaders <= pvaluesHeadersList
    
    for i in range(len(dataPairs)):
        pair = dataPairs[i]
        
        td1 = html.TD(pair["dataset_id"])
        td2 = html.TD(pair["sample_1"])
        td3 = html.TD(pair["sample_1_size"])
        td4 = html.TD(pair["sample_2"])
        td5 = html.TD(pair["sample_2_size"])
        td6 = html.TD(pair["gene"])
        td7 = html.TD(pair["probe"])
        td8 = html.TD(str(round(float(pair["pvalue"]),2)))
        td9 = html.TD(str(round(float(pair["tstat"]),2)))

        tdList = [td1, td2, td3, td4, td5, td6, td7, td8, td9]

        if (i % 2 == 1):
            for td in tdList:
                td.style.background = "#F7F7F7"
                
        row = html.TR()        
        row <= tdList  
        pvaluesTableRows.append(row)
    
    pvaluesTableBody <= pvaluesTableHeaders
    pvaluesTableBody <= pvaluesTableRows
    
    pvaluesTable <= pvaluesTableBody
    
##############################################################

def draw_home3():
    dataset_list_table = html.TABLE(cellspacing=0, border=1, bordercolor="lightgray", id="dataset_list_table")
    tableBody = html.TBODY()
    headers = html.TR()

    tableBody.style.border = "thin solid lightgray"

    # to clear list, do this:    del left_table_rows [:]
    dataset_list_table_rows = []
    
    link = html.A('\u2191\u2193', href="#", Class="sort_link")
    link.bind('click',lambda ev:sort_by_col(ev,headers,dataset_list_table_rows,tableBody,False))
    
    link_num = html.A('\u2191\u2193', href="#", Class="sort_link")
    link_num.bind('click',lambda ev:sort_by_col(ev,headers,dataset_list_table_rows,tableBody,True))

    hD = html.TH('Dataset ID' + link)
    hP = html.TH('PubMed ID' + link.clone())
    
    hList = [hD, hP]

    for h in hList:
        h.style.background = "#E0E0E0"
        h.style.font = "16px verdana"
        
    h = None
    
    headers <= hList

    for i in range(0):
        row = html.TR()

        button = html.BUTTON("GDS123" + str(i), row = str(i), gds = "GDS123")
        button.style.font = "16px verdana"
        #button.style.textAlign = "center"

        button.value = "GDS123" + str(i)
        button.bind('mouseout', mouse_out_button)
        button.bind('mouseover', mouse_over_button)
        button.bind('click', click_dataset_id_button)
        button.style.border = "thin solid gray"
        button.style.background = "#EEEEEE"
        button.style.color = "#505050"
    
        td1 = html.TD(button)
        td1.style.textAlign = "center"
        
        td2 = html.TD(html.A("7896544" + str(10-i), href="http://www.ncbi.nlm.nih.gov/pubmed/?term=17262812", target="_blank"))
        td2.style.textAlign = "center"

        tdList = [td1, td2]

        if (i % 2 == 1):
            for td in tdList:
                td.style.background = "#F7F7F7"
        
        row <= tdList
        dataset_list_table_rows.append(row)
    
    tableBody <= headers
    tableBody <= dataset_list_table_rows
    
    dataset_list_table <= tableBody
    dataset_list_table.style.font = "16px verdana"
    dataset_list_table.style.color = "#303030"
    
    panel = document["main_panel"]
    #panel <= dataset_list_table

    ###################################
    
    pvaluesTable = html.TABLE(cellspacing=0, border=1, bordercolor="lightgray", id="pvalue_list_table")
    pvaluesTable.width = 985
    
    pvaluesTableBody = html.TBODY()
    pvaluesTableHeaders = html.TR()

    pvaluesTableBody.style.border = "thin solid lightgray"

    # to clear list, do this:    del left_table_rows [:]
    pvaluesTableRows = []
    
    pvaluesLink = html.A('\u2191\u2193', href="#", Class="sort_link")
    pvaluesLink.bind('click',lambda ev:sort_by_col(ev,pvaluesTableHeaders,pvaluesTableRows,pvaluesTableBody,False))
    
    pvaluesLinkNum = html.A('\u2191\u2193', href="#", Class="sort_link")
    pvaluesLinkNum.bind('click',lambda ev:sort_by_col(ev,pvaluesTableHeaders,pvaluesTableRows,pvaluesTableBody,True))

    h1 = html.TH('Dataset ID' + pvaluesLink)
    h2 = html.TH('Sample1' + pvaluesLink.clone())
    h3 = html.TH('Size1' + pvaluesLinkNum)
    h4 = html.TH('Sample2' + pvaluesLink.clone())
    h5 = html.TH('Size2' + pvaluesLinkNum.clone())
    h6 = html.TH('Gene' + pvaluesLink.clone())
    h7 = html.TH('Probe' + pvaluesLink.clone())
    h8 = html.TH('P-value x1E6' + pvaluesLinkNum.clone())
    h9 = html.TH('T-stat' + pvaluesLinkNum.clone())
                             
    pvaluesHeadersList = [h1, h2, h3, h4, h5, h6, h7, h8, h9]

    for h in pvaluesHeadersList:
        h.style.background = "#E0E0E0"
        h.style.font = "16px verdana"
        
    pvaluesTableHeaders <= pvaluesHeadersList
    
    pvaluesTableBody <= pvaluesTableHeaders
    pvaluesTableBody <= pvaluesTableRows
    
    pvaluesTable <= pvaluesTableBody
    pvaluesTable.style.font = "16px verdana"
    pvaluesTable.style.color = "#303030"

    div1 = html.DIV()
    div1.style.overflow = "scroll";
    div1.height = 300
    div1.width = 250
    div1 <= dataset_list_table

    div2 = html.DIV()
    div2.style.overflow = "scroll";
    div2.height = 300
    div2.width = 1000
    div2 <= pvaluesTable

    doubleTable = html.TABLE()
    doubleTableBody = html.TBODY()
 
    downloadFilesRow = html.TR()
    doubleTableRow = html.TR()

    tdLeft = html.TD()
    tdLeft <= div1
    tdLeft.style.padding = "0px 20px 0px 0px"
    
    tdRight = html.TD()
    tdRight <= div2
    
    tdDownloadLeft = html.TD()
    tdDownloadRight = html.TD()

    aLeft = html.A('<img src="download_icon.jpg" height=20 width=20> Download', id='aLeft')
    aLeft.style.font = "16px verdana"
    aLeft.style.color = "#303030"
    tdDownloadLeft <= aLeft

    aRight = html.A('<img src="download_icon.jpg" height=20 width=20> Download', id='aRight')
    aRight.style.font = "16px verdana"
    aRight.style.color = "#303030"
    tdDownloadRight <= aRight

    downloadFilesRow <= [tdDownloadLeft, tdDownloadRight]
    doubleTableRow <= [tdLeft, tdRight]

    doubleTableBody <= downloadFilesRow
    doubleTableBody <= doubleTableRow
    doubleTable <= doubleTableBody

    panel <= doubleTable
    
    #panel <= div1
    #panel <= div2
    
    #panel <= [ dataset_list_table, pvaluesTable ]
    
##############################################################

def draw_home_samples(sample1,sample2):
    panel = document["main_panel"]
    
    table = html.TABLE()
    table.style.fontSize = "large"
    table.style.font = "16px verdana"
    
    tableBody = html.TBODY()
    row = html.TR()

    tableBody.style.verticalAlign = "center"
    row.style.verticalAlign = "center"

    table.style.background = "#F7F7F7"
    table.style.padding = "10px 25px 10px 10px"
    
    label = html.LABEL("Select samples to search:")
    label.style.verticalAlign = "center"
    label.style.marginRight = "10px"

    td1 = html.TD()
    td1 <= label
    row <= td1

    #op11 = html.OPTION(sample1)
    #op12 = html.OPTION(sample2)

    #op21 = html.OPTION(sample1)
    #op22 = html.OPTION(sample2)
    
    sel1 = html.SELECT([], id="selector_samples_1", font_size=16)
    sel1.style.fontSize = "large"
    sel1.style.verticalAlign = "center"
    sel1.style.marginRight = "20px"
    sel1.style.width = "300px"
    
    td2 = html.TD()
    td2 <= sel1
    row <= td2

    sel2 = html.SELECT([], id="selector_samples_2", font_size=16)
    sel2.style.fontSize = "large"
    sel2.style.verticalAlign = "center"
    sel2.style.marginRight = "0px"
    sel2.style.width = "300px"
    
    td3 = html.TD()
    td3 <= sel2
    row <= td3

    b = html.BUTTON('Search', id = "search_subsets")
    button_style_default(b)
    b.bind('click', click_search_subsets)
    b.bind('mouseout', mouse_out_search_subsets)
    b.bind('mouseover', mouse_over_search_subsets)
    b.style.verticalAlign = "center"
    b.style.marginTop = "0px"
    b.style.marginBottom = "0px"
    
    td4 = html.TD()
    td4.style.verticalAlign = "center"
    td4 <= b
    row <= td4
     
    tableBody <= row
    table <= tableBody

    panel <= table
    panel <= html.BR()

##############################################################

def draw_home_title_description():
    panel = document["main_panel"]
    
    table = html.TABLE()
    table.style.fontSize = "large"
    table.style.font = "16px verdana"
    
    tableBody = html.TBODY()
    row = html.TR()

    tableBody.style.verticalAlign = "center"
    row.style.verticalAlign = "center"

    table.style.background = "#F7F7F7"
    table.style.padding = "10px 10px 10px 10px"
    
    label = html.LABEL("Details for dataset:", id = "label_details_for_dataset")
    label.style.verticalAlign = "center"
    label.style.marginRight = "10px"
    
    td1 = html.TD()
    td1 <= label
    td1.style.width = "200px"
    row <= td1

    div2 = html.DIV()
    div2.style.overflow = "scroll";
    div2.height = 100
    div2.width = 250

    title_text_area = html.TEXTAREA("Title:", id = "dataset_title")
    title_text_area.readOnly = True
    #title_text_area.disabled = True
    title_text_area.style.font = "14px verdana"
    title_text_area.rows = 10
    title_text_area.cols = 26
    div2 <= title_text_area

    td2 = html.TD()
    td2 <= div2
    row <= td2
    
    div3 = html.DIV()
    div3.style.overflow = "scroll";
    div3.height = 100
    div3.width = 450

    description_text_area = html.TEXTAREA("Description:", id = "dataset_description")
    description_text_area.readOnly = True
    #description_text_area.disabled = True
    description_text_area.style.font = "14px verdana"
    description_text_area.rows = 10
    description_text_area.cols = 51
    div3 <= description_text_area

    td3 = html.TD()
    td3 <= div3
    row <= td3

    tableBody <= row
    table <= tableBody
    panel <= table
    panel <= html.BR()
    
##############################################################

def draw_home():
    panel = document["main_panel"]
    
    panel <= "Use GeneXpresso search and analysis tools to analyze differences in gene expressions"\
        " between DNA microarray datasets.  Refer to the User Guide for detailed instructions,"\
        " and feel free to contact us at genexpresso@gmail.com if you have any questions or feedback."
    panel <= html.BR()
    panel <= html.BR()

    draw_home1()
    draw_home2()
    draw_home_samples('','')
    draw_home_title_description()
    draw_home3()

    panel <= html.BR()
    p = html.P("Powered by ")
    p.style.textAlign = "left"
    p.style.fontSize = "small"
    p.style.font = "12px verdana"                    
    panel <= p
    panel <= html.IMG(src="gcp.png", width="150")
    
##############################################################

def draw_guide():
    panel = document["main_panel"]
    guide = html.OBJECT(width="1000", height="1000", data="GeneXpressoUserGuide.pdf")

    download = html.A('<img src="download_icon.jpg" height=20 width=20> Download User Guide', target="_blank")
    download.style.font = "16px verdana"
    download.style.color = "#303030"
    download.href = "GeneXpressoUserGuide.pdf"

    panel <= download
    panel <= html.BR()
    panel <= html.BR()
    panel <= guide
    
##############################################################

def draw_about():
    panel = document["main_panel"]
    
    panel.style.fontSize = "large"
    panel.style.font = "20px verdana"
    
    panel <= html.BR()

    panel <= "GeneXpresso enables researchers to search and analyze large DNA microarray datasets " \
        "without having to write a single line of code.  The users can download results of the analysis " \
        "for further exploration.  We use a public DNA microarray database at the "

    panel <= html.A("National Center for Biotechnology Information", href='http://www.ncbi.nlm.nih.gov/gds/')

    panel <= " as our source of raw gene expression data.  " \
        "The current version of GeneXpresso includes " \
        "data for Homo sapiens only, however we can add datasets for other species as well upon request."

    panel <= html.BR()
    panel <= html.BR()

    panel <= "Watch "
    panel <= html.A("GeneXpresso instructional video on YouTube.",
                    href='https://www.youtube.com/watch?v=vSKzyA4y614', target='_blank')
    
    panel <= html.BR()
    panel <= html.BR()
    
    panel <= "If your lab is in the New York City area, please contact us at genexpresso@gmail.com to schedule " \
        " a tutorial.  We can come to your lab to do a demonstration on how to use the GeneXpresso "\
        "analysis tools for your research."

    panel <= html.BR()
    panel <= html.BR()
    panel <= html.BR()

    about_sean = html.TABLE()
    row = html.TR()   
    left = html.TD(width=270)
    right = html.TD()

    about_sean.style.verticalAlign = "top"
    row.style.verticalAlign = "top"
    right.style.verticalAlign = "top"
    left.style.textAlign = "center"
    left.style.padding = "0px 30px 0px 0px"

    left <= html.IMG(src="sean-portrait-small.png", width="150")
    left <= html.BR()
    left <= html.STRONG("Sean Vaysburd")
    left <= html.BR()
    left <= "Founder, Head of "
    left <= html.BR()
    left <= "Research and Technology" 
    left <= html.BR()
    left <= html.A("Sean's Resum&#233;", href='SeanVaysburdResume2017.pdf', target='_blank')

    right <= "Sean Vaysburd founded GeneXpresso to make it easy for genetics researchers " \
        "to quickly analyze large DNA microarray gene expression datasets without " \
        "having to write any computer software. "

    right <= html.BR() 
    right <= html.BR()

    right <= "Over the summer of 2015, Sean did a project aiming to " \
        "analyze the statistical significance of gene expression numbers for groups of people with " \
        "different disease states, based on over 70 DNA microarray data files with 50,000+ gene expression " \
        "probes in each dataset.  While working on this project, Sean found several disease groups with " \
        " similar gene expression clusters. " \
        "Some of those findings were quite unexpected and could indicate previously unknown relationships " \
        "between different diseases at the gene-expression level.  Inspired by these results, " \
        "Sean set a goal of making DNA microarray search and analysis tools that he wrote " \
        "available to biomedical researchers everywhere.  GeneXpresso is a result of this pursuit."

    right <= html.BR()
    right <= html.BR()

    right <= "Sean is currently a senior at Stuyvesant High School in New York City. " \
        "He works as a research volunteer at Dr. Pei's Microbiome Lab at the NYU School of Medicine. "

    row <= [left, right]
    about_sean <= row

    about_sean <= html.BR()

    # Sam
    row = html.TR()
    left = html.TD(width=270)
    right = html.TD()
    
    about_sean.style.verticalAlign = "top"
    row.style.verticalAlign = "top"
    right.style.verticalAlign = "top"
    left.style.textAlign = "center"
    left.style.padding = "0px 30px 0px 0px"
    
    left <= html.IMG(src="sam-portrait-small.png", width="150")
    left <= html.BR()
    left <= html.STRONG("Samuel Ramos")
    left <= html.BR()
    left <= "Team member,"
    left <= html.BR()
    left <= "Head of Marketing"
    left <= html.BR()

    right <= html.BR()
    right <= html.BR()
    right <= "Samuel Ramos is a senior at Stuyvesant High School. In 2016, he studied at Brooklyn’s Genspace community laboratory learning how to use CRISPr +cas9 technology. During the summer of 2017 he developed a cell breast cancer culture study with Dr. Harry Ostrer and Dr. John Loke at Albert Einstein School of Medicine."

    row <= [left, right]
    about_sean <= row
    about_sean <= html.BR()
    about_sean <= html.BR()

    # Max
    row = html.TR()
    left = html.TD(width=270)
    right = html.TD()
    
    about_sean.style.verticalAlign = "top"
    row.style.verticalAlign = "top"
    right.style.verticalAlign = "top"
    left.style.textAlign = "center"
    left.style.padding = "0px 30px 0px 0px"
    
    left <= html.IMG(src="max-portrait-small.png", width="150")
    left <= html.BR()
    left <= html.STRONG("Max Vaysburd")
    left <= html.BR()
    left <= "Team Member,"
    left <= html.BR()
    left <= "Head of Operations"
    left <= html.BR()

    right <= html.BR()
    right <= html.BR()
    right <= "Max Vaysburd is a freshman at Stuyvesant High School.  " \
        "He has participated in AMC-10, AMC-12, AIME, and ARML competitions " \
        "and is currently on the Stuyvesant Math Team.  Max has completed the " \
        "online Machine Learning class on Coursera."

    row <= [left, right]
    about_sean <= row

    
    panel <= about_sean

    panel <= html.P()
    
    #panel <= "Sean enjoys studying and researching biology, genetics, and computer programming. " \
    #    "In his spare time he likes painting pictures of nature and animals on seashells and ceramic tiles."


    #center = html.CENTER()
    #panel <= center

    panel <= html.BR()
    panel <= html.BR()
    panel <= html.BR()
    
    #panel <= html.IMG(src="parrot.jpg", width="200")
    #p = html.P("Painting of a parrot by Sean")
    #p.style.fontSize = "small"
    #p.style.fontStyle = "italic"
    #panel <= p

##############################################################

def draw_contact():
    panel = document["main_panel"]

    panel <= "We appreciate feedback and ideas for making GeneXpresso.com more useful for your research."\
        " If you have suggestions, comments, or requests for specific datasets (microarray or other types) "\
        "that you would like to be able to analyze using GeneXpresso, or if you would like to schedule "\
        "a demonstration / tutorial on how to use GeneXpresso analysis tools, feel free to contact us at "

    panel <= html.A("genexpresso@gmail.com.", href = "mailto:genexpresso@gmail.com")


def draw_contact_bigButton():
    panel = document["main_panel"]

    p = html.P("Send an email to GeneXpresso:")
    p.style.textAlign = "center"
    p.style.fontSize = "large"
    p.style.font = "20px verdana"
    p.style.textAlign = "center"
    
    panel <= html.BR()
    panel <= html.BR()
    panel <= html.BR()
    panel <= html.BR()

    #panel <= p
    
    form = html.FORM()
    form.style.fontSize = "large"
    form.style.font = "20px verdana"
    form.action = "mailto:genexpresso@gmail.com"
    form.method = "POST"
    form.style.textAlign = "center"
    
    global buttonSendEmail
    buttonSendEmail = html.INPUT()
    buttonSendEmail.type = "submit"
    buttonSendEmail.value = "Send"
    button_style_default(buttonSendEmail)
    buttonSendEmail.bind('mouseout', mouse_out_send_email)
    buttonSendEmail.bind('mouseover', mouse_over_send_email)
    
    form <= buttonSendEmail
    panel <= form

##############################################################

def setup_top_panel():
    top_panel = document["about_panel"]

    table = html.TABLE()
    tableBody = html.TBODY()
    row = html.TR()

    # html style properties:
    # http://www.w3schools.com/jsref/dom_obj_style.asp

    global buttonHome
    buttonHome = html.BUTTON('Data Analysis')
    button_style_default(buttonHome)
    buttonHome.bind('click', click_home)
    buttonHome.bind('mouseout', mouse_out_home)
    buttonHome.bind('mouseover', mouse_over_home)

    global buttonAbout
    buttonAbout = html.BUTTON('About')
    button_style_default(buttonAbout)
    buttonAbout.bind('click', click_about)
    buttonAbout.bind('mouseout', mouse_out_about)
    buttonAbout.bind('mouseover', mouse_over_about)

    global buttonGuide
    buttonGuide = html.BUTTON('User Guide')
    button_style_default(buttonGuide)
    buttonGuide.bind('click', click_guide)
    buttonGuide.bind('mouseout', mouse_out_guide)
    buttonGuide.bind('mouseover', mouse_over_guide)
    
    global buttonContact
    buttonContact = html.BUTTON('Contact')
    button_style_default(buttonContact)
    buttonContact.bind('click', click_contact)
    buttonContact.bind('mouseout', mouse_out_contact)
    buttonContact.bind('mouseover', mouse_over_contact)
    
    row <= html.IMG(src="genexpresso.png", width="100")
    row <= buttonHome
    row <= buttonGuide
    row <= buttonAbout
    row <= buttonContact
    
    tableBody <= row
    table <= tableBody
    top_panel <= table

    
def selectQueryType(ev):
    selector = document["query_selector"]
    document <= html.BR() + "selected value: " + selector.value

##############################################################
    
def main():
    setup_top_panel()
    draw_about()
    
main()
