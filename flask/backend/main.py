from flask import Flask, request, session
from utils import *
import os, re, glob, shutil
import zipfile
import asyncio
from functools import partial
from collections import Counter

app = Flask(__name__)
app.secret_key = 'caompaniesqa'

checkor = []
# session["checkor"] = []
call_count = Counter()

@app.route('/api/healthcheck',methods = ["GET"])
def hello():
    # company_names = get_companies("elasticdb")
    # print(company_names)
    return {"msg": 'Hello World!'}

@app.route('/api/delete2',methods = ["POST"])
def delete2():
    data = request.json
    name = data["name"]
    company_names = get_companies("elasticdb")
    f = find_most_similar_name(name,company_names)
    refresh_index("elasticdb")
    return {f"msg": f}

@app.route('/api/delete',methods = ["POST"])
def delete():
    delete_data()
    create_index("elasticdb")
    refresh_index("elasticdb")
    return {"msg": 'Deleted'}


@app.route('/api/qa', methods=['POST'])
def query():
    async def handle_query(question):
        # Call the `api_fun` function asynchronously
        loop = asyncio.get_running_loop()
        answer = await loop.run_in_executor(None, api_fun, question)
        return {"Answer": answer}

    # Parse incoming JSON request data
    data = request.json
    question = data["question"]

    # Start the event loop and run the coroutine
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    answer = loop.run_until_complete(handle_query(question))
    loop.close()

    # Return the answer as a JSON response
    return answer   


@app.route('/api/qa2',methods = ["POST"])
def query2():
    data = request.json
    question = data["question"]
    answer = api_fun2(question)
    return {"Answer": answer}


@app.route('/api/feeddata',methods = ["POST"])
def feeddata():
    # data = request.json
    nfiles = []
    kfiles = []
    company_names = get_companies("elasticdb")
    # print(company_names)
    # nfiles = data["n_files"]

    if "companies" in os.listdir("."):shutil.rmtree("companies")
    os.mkdir("companies")

    xfiles = request.files["file"]
    afiles = xfiles.filename
    if not afiles.endswith('.txt'):
        return "Enter a txt File"
    file_path  = os.path.join("companies",afiles)
    xfiles.save(file_path)
    nfiles.append(afiles)
    print(nfiles, type(nfiles))

    for i in range(len(nfiles)):
            kfiles.append(nfiles[i])
            if re.search(r"\..*\.", nfiles[i]):
                nfiles[i] = re.sub(r"\..*", "", nfiles[i])
                nfiles[i] = nfiles[i] + "."
            else:
                nfiles[i] = re.sub(r"\..*", "", nfiles[i])
            # nfiles[i] = n
    print(kfiles)
    session["checkor"] = kfiles
    call_count['retrival'] = 0
    # for file in kfiles:
    async def process_file(file):
        print(file)
        x = cname(file)
        if x not in company_names:
            print(x)
            retrival(x)
            print("Retrieval successful")
            call_count['retrival'] += 1
            print("inserted")
        else:
            print("file already exists")

    async def main():
        # create a coroutine for each file
        coroutines = [process_file(file) for file in kfiles]

        # gather all coroutines
        await asyncio.gather(*coroutines)

    # create an event loop and run the coroutine
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_in_executor(None, partial(loop.run_until_complete, main()))

    return 'inserting'
    
@app.route('/api/feeddata1',methods = ["POST"])
def feeddata1():
    # if check not in session:
    #     session["check"] = 0
    zip_file = request.files.get("file")
    afiles = zip_file.filename
    print(afiles)
    if not afiles.endswith('.zip'):
        return "Enter a Zip File"

    company_names = get_companies("elasticdb")
    tfiles = []
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        file_names = zip_ref.namelist()
        print(file_names[0])

        if not os.path.isdir(f'./{file_names[0]}'):
            if file_names[0] in os.listdir("."): os.remove(file_names[0])
            if "companies" in os.listdir("."):shutil.rmtree("companies")
            os.mkdir("companies")
            zip_ref.extractall('./companies')
            txt_file_names = file_names
        else:
            if file_names[0] in os.listdir("."): os.remove(file_names[0])
            if "companies" in os.listdir("."):shutil.rmtree("companies")
            zip_ref.extractall('./')  # Extract the entire archive to the current directory
            if file_names[0] != "companies":
                os.rename(file_names[0], "companies")
            txt_file_names = glob.glob(f'./{file_names[0]}/**/*.txt', recursive=True) 
            txt_file_names = [f for f in file_names if f.startswith(file_names[0]) and f.endswith('.txt')]
            txt_file_names = [os.path.basename(f) for f in txt_file_names]
    session["checkor"] = txt_file_names
    call_count['retrival'] = 0
    async def process_file(file):
        print(file)
        
        x = cname(file)
        if x not in company_names:
            print(x)
            retrival(x)
            call_count['retrival'] += 1
            print("Retrieval successful")
            print("inserted")
        else:
            print("file already exists")

    async def main():
        # create a coroutine for each file
        coroutines = [process_file(file) for file in txt_file_names]

        # gather all coroutines
        await asyncio.gather(*coroutines)

    # create an event loop and run the coroutine
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_in_executor(None, partial(loop.run_until_complete, main()))

    return 'inserting'

@app.route('/api/checker', methods = ["GET"])
def checker():
    if session.get('checkor'):
        n = len(session.get('checkor'))
    else: n = 0
    # session["checkor"] = []
    # n1 = session.get('check')
    return f"{call_count['retrival']} of {n} files are inserted...."

# @app.route('/api/feeddata1',methods = ["POST"])
# def feeddata1():
#     # data = request.json
#     tfiles = []
#     company_names = get_companies("elasticdb")
#     # Get the uploaded zip file
#     zip_file = request.files.get("file")
#     afiles = zip_file.filename
#     print(afiles)
#     if afiles.endswith('.zip'):
#         with zipfile.ZipFile(zip_file, 'r') as zip_ref:
#             # Get the list of file names in the zip file
            
#             file_names = zip_ref.namelist()
#             print(file_names[0])

#             if not os.path.isdir(f'./{file_names[0]}'):
#                 if file_names[0] in os.listdir("."): os.remove(file_names[0])
#                 if "companies" in os.listdir("."):shutil.rmtree("companies")
#                 os.mkdir("companies")
#                 zip_ref.extractall('./companies')
#                 txt_file_names = file_names
#             else:

#                 if file_names[0] in os.listdir("."): os.remove(file_names[0])
#                 if "companies" in os.listdir("."):shutil.rmtree("companies")
#                 # os.mkdir("companies")
#                 # print(file_names[0].rstrip('/'))
#                 zip_ref.extractall('./')  # Extract the entire archive to the current directory
#                 if file_names[0] != "companies":
#                     os.rename(file_names[0], "companies")
#                 txt_file_names = glob.glob(f'./{file_names[0]}/**/*.txt', recursive=True) 
#                 txt_file_names = [f for f in file_names if f.startswith(file_names[0]) and f.endswith('.txt')]
#                 txt_file_names = [os.path.basename(f) for f in txt_file_names]

#         # Process each text file in the zip file
#         # for file_name in txt_file_names:
#         #     nfiles = []
#         #     # print(file_name)
#         #     nfiles.append(file_name)
#         #     for i in range(len(nfiles)):
#         #         tfiles.append(nfiles[i])
#         #         if re.search(r"\..*\.", nfiles[i]):
#         #             nfiles[i] = re.sub(r"\..*", "", nfiles[i])
#         #             nfiles[i] = nfiles[i] + "."
#         #         else:
#         #             nfiles[i] = re.sub(r"\..*", "", nfiles[i])
#             # print(tfiles)
#             # print(txt_file_names)
#             for file in txt_file_names:
                    
#                         print(file)
#                         x = cname(file)
#                         if x not in company_names:
#                             print(x)
#                             retrival(x)
#                         else:
#                             print("file already exists")
#         return 'inserted'
#     else:
#         return "Enter a Zip File"

if __name__ == '__main__':
    app.run()
