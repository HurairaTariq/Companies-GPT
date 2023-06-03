from sentence_transformers import SentenceTransformer, util
from elasticsearch import Elasticsearch
import re, os
import time
import openai
from openai import Embedding
from openai.embeddings_utils import get_embeddings, cosine_similarity
import scipy

api_key = '***************************************'
openai.api_key = api_key

EMBEDDING_DIMS = 768
ENCODER_BOOST = 10
headinglist = []
new_sentences = []

# Initialie the bert model to create embeddings
sentence_transformer = SentenceTransformer("sentence-transformers/multi-qa-mpnet-base-dot-v1")
# Connect to Elastic Search
es_client = Elasticsearch("http://localhost:9200", verify_certs=False, request_timeout=60)
# es_client = Elasticsearch("http://elasticsearch:9200", verify_certs=False, request_timeout=600)


def find_most_similar_name(name, name_list):
    # Calculate the embeddings for the input name and the list of names
    if not name_list:
        return "DB is empty, Insert files First"
    name_embedding = sentence_transformer.encode(name)
    name_list_embeddings = sentence_transformer.encode(name_list)

    # Calculate the cosine similarity between the input name embedding and the list of name embeddings
    similarities = 1 - scipy.spatial.distance.cdist([name_embedding], name_list_embeddings, "cosine")[0]

    # Find the index of the most similar name in the list
    most_similar_idx = similarities.argmax()

    if similarities[most_similar_idx] > 0.7:
        print(name_list[most_similar_idx])
        name = name_list[most_similar_idx]
        x = delete_company(name)
        # Return the most similar name
        return name
    else:
        return "No file found"
    
def delete_data():
    index_name = 'elasticdb'  # replace with your index name

    query = {
        'query': {
            'match_all': {}
        }
    }

    # Delete all documents in the index
    es_client.delete_by_query(index=index_name, body=query, wait_for_completion=True)

def delete_company(name):
    result = es_client.delete_by_query(
        index="elasticdb", 
        body={
  "query": {
    "match": {
      "company": {
        "query": name,
        "minimum_should_match": "100%"
      }
    }
  }
}
    )
    print(result)
    return result


def create_index(index_name) -> None:
    es_client.options(ignore_status=404).indices.delete(index=index_name)
    es_client.options(ignore_status=400).indices.create(
        index=index_name,
        mappings={
            "properties": {
                "embedding": {
                    "type": "dense_vector",
                    "dims": EMBEDDING_DIMS,
                },
                "context": {
                    "type": "text",
                },
                "company": {
                    "type": "text",
                },
            }
        }
    )

def refresh_index(index_name) -> None:
    es_client.indices.refresh(index=index_name)

# Add values to the database
def index_context(contexts, index_name, company):
    for context in contexts:
        context1 = context
        embedding = sentence_transformer.encode(context1)
        data = {
            "context": context1,
            "embedding": embedding,
            "company": company
        }
        
        es_client.options(max_retries=0).index(
            index=index_name,
            document=data
        )
    
def get_companies(index_name):
    try:
        companies = set()
        result = es_client.search(
            index=index_name, 
            body={"query": {"match_all": {}}},
            scroll='1m'
        )
        scroll_id = result['_scroll_id']
        hits = result['hits']['hits']
        while len(hits) > 0:
            for hit in hits:
                companies.add(hit['_source']['company'])
            result = es_client.scroll(scroll_id=scroll_id, scroll='1m')
            scroll_id = result['_scroll_id']
            hits = result['hits']['hits']
        return list(companies)
    except:
        return []


def query_by_company(index_name, company_name, top_n):
    result = es_client.search(
        index=index_name,
        body={
            "query": {
                "match": {
                    "company": company_name
                }
            }
        },
        size=top_n
    )
    hits = result["hits"]["hits"]
    clean_result = []
    for hit in hits:
        clean_result.append({
            "context": hit["_source"]["context"]
        })
    return hits

def query_question(question: str, company: str, index_name: str, top_n: int):
    embedding = sentence_transformer.encode(question)
    es_result = es_client.search(
        index=index_name,
        size=top_n,
        from_=0,
        source=["context"],
        query={
            "script_score": {   
                 "query": {
                    "bool": {
                        "must":[
                            {"match": {"company": company}}
                        ],
                        "should": [
                            {"match": {"context": question}}
                        ]
                    }
                },
                # "query": {
                #     "match": {
                #         "context": question,
                #         "company": company
                #     }
                # },
                "script": {
                    "source": """
                            (cosineSimilarity(params.query_vector, "embedding") + 1)* params.encoder_boost + _score
                        """,
                    "params": {
                        "query_vector": embedding,
                        "encoder_boost": ENCODER_BOOST,
                    },
                },
            }
        }
    )
    hits = es_result["hits"]["hits"]
    clean_result = []
    print(hits)
    for hit in hits:
        clean_result.append({
            "context": hit["_source"]["context"],
            "score": hit["_score"],
        })
    
    return clean_result

def cname(fname):
    filepath = os.path.abspath(f'./companies/{fname}')
    with open(filepath, "r", encoding="utf-8") as foo:
        lines = foo.readlines()
    line = lines[0].strip('\n').replace("/", "_").replace("\\", "-")
    
    new_filepath = os.path.join(os.path.dirname(filepath), line)
    # print(filepath, new_filepath)
    if filepath != new_filepath:
        os.rename(filepath, new_filepath)
    return line

def headings(fname):
    with open (f'./companies/{fname}', "r", encoding="utf-8") as foo:
        lines = foo.readlines()
    x = "PARAGRAPHS"
    for i, line in enumerate(lines):    
        if x in line:
            a = i
            break
    if a is not None:
        for a, line in enumerate(lines[a+1:]):
            if "-----" in line:
                break
            elif line == '\n':
                continue
            else:
                headinglist.append(line.strip())

    headinglist.append('-----')
    # print(headinglist)
    return headinglist
    
def regi_check(mylist):
        alphabets= "([A-Za-z])"
        prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
        suffixes = "(Inc|Ltd|Jr|Sr|Co)"
        starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
        acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
        websites = "[.](com|net|org|io|gov)"
        digits = "([0-9])"
        mylist = " " + mylist + "  "
        mylist = mylist.replace("\n"," ")
        mylist = re.sub(prefixes,"\\1<prd>",mylist)
        mylist = re.sub(websites,"<prd>\\1",mylist)
        mylist = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",mylist)
        if "..." in mylist: mylist = mylist.replace("...","<prd><prd><prd>")
        if "Ph.D" in mylist: mylist = mylist.replace("Ph.D.","Ph<prd>D<prd>")
        mylist = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",mylist)
        mylist = re.sub(acronyms+" "+starters,"\\1<stop> \\2",mylist)
        mylist = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",mylist)
        mylist = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",mylist)
        mylist = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",mylist)
        mylist = re.sub(" "+suffixes+"[.]"," \\1<prd>",mylist)
        mylist = re.sub(" " + alphabets + "[.]"," \\1<prd>",mylist)
        if "”" in mylist: mylist = mylist.replace(".”","”.")
        if "\"" in mylist: mylist = mylist.replace(".\"","\".")
        if "!" in mylist: mylist = mylist.replace("!\"","\"!")
        if "?" in mylist: mylist = mylist.replace("?\"","\"?")
        mylist = mylist.replace(".",".<stop>")
        mylist = mylist.replace("?","?<stop>")
        mylist = mylist.replace("!","!<stop>")
        mylist = mylist.replace("<prd>",".")
        sentences = mylist.split("<stop>")
        sentences = sentences[:-1]
        sentences = [s.strip() for s in sentences]

        for word in list(sentences):  # iterating on a copy since removing will mess things up
            if word == '.':
                sentences.remove(word)
        sentence_chunk = ''
        n = 7
        for i in range(len(sentences)):
            if (i+1)%n==0: 
                sentence_chunk += sentences[i]
                new_sentences.append(sentence_chunk)
                sentence_chunk = '' 
            else:
                sentence_chunk += sentences[i]
        if sentence_chunk:
            new_sentences.append(sentence_chunk)
        # return new_sentences
    
def text_data(fname):
    with open (f'./companies/{fname}', "r", encoding="utf-8") as foo:
        lines = foo.readlines()
    x = "TEbXT"
    length = len(headinglist)
    for cou in range(length):
        head1 = headinglist[cou]
        if cou+1 < (length):
            head2 = headinglist[cou+1]
        # print(head1, head2)
        mylist = []
        for i, line in enumerate(lines):
            if x in line:
                a = i #303
                break

        for k, line in enumerate(lines[a+1:]):
            if head1 in line:
                if lines[i+1].strip() == "":
                    a = k+a+1
                    break
          
        if a is not None:
            for k, line in enumerate(lines[a+2:]):
                if head2 in line:
                    break
                elif line == '\n':
                    continue
                elif line == ' ':
                    continue
                else:
                    mylist.append(line.strip())
        # print(mylist)
        mylist = '.'.join(mylist)
        regi_check(mylist)
    return new_sentences

def text1_data(fname):
    with open(f'./companies/{fname}', "r", encoding="utf-8") as foo:
        lines = foo.readlines()
    a = None
    mylist = []
    x = "EARNINGS CALL"
    for i, line in enumerate(lines):    
        if x in line:
            a = i
            break
    if a is not None:
        for a, line in enumerate(lines[a+1:]):
            if "-----" in line:
                break
            elif line == '\n':
                continue
            else:
                mylist.append(line)
    mylist = '.'.join(mylist)
    regi_check(mylist)

def string_convert(x):
    string_answer = ''
    for i in range(len(x)):
        valuess = list(x[i].values())
        string_answer += valuess[0] + '.'

    return string_answer

def get_info(context, query):
    if not context:
        return "There's no data of this company"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Given the question and the data we have to get the most accurate answer from the data according to the question.\nData: {context}\nQuestion: {query}\nAnswer:",
        temperature=0,
        max_tokens=250,
        frequency_penalty=1,
        presence_penalty=1,
    )
    return response.choices[0].text.strip()

def get_info2(context, query, name):
    if not context:
        return "There's no data of this company"
    response = openai.Completion.create(
        engine="text-curie-001",
        prompt=f"Given the question and the data we have to get the most accurate answer of company from the data according to the question.\ncompany: {name}\nData: {context}\nQuestion: {query}\nAnswer:",
        temperature=0,
        max_tokens=250,
        frequency_penalty=1,
        presence_penalty=1,
    )
    return response.choices[0].text.strip()


def extract_cname(query):
    response = openai.Completion.create(
        engine = "text-davinci-003",
        prompt=f"Extract company name with 100% accuracy from the given question and seperate them by comma and skip every other word if do not find any return empty string.question: {query}Company name:",
        temperature=0,
        max_tokens=100,
        frequency_penalty=0,
        presence_penalty=0,
    )
    return response.choices[0].text

def q_general(query):
    response = openai.Completion.create(
        engine = "text-davinci-003",
        prompt=f"Extract main words from the question.question: {query}answer:",
        temperature=0,
        max_tokens=100,
        frequency_penalty=0,
        presence_penalty=0,
    )
    return response.choices[0].text


def final_prompt(data, query):
    
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=f"data is the answers according to question make it in a readable form and dont repeat information.\ndata:{data}\nquesiton:{query}\nAnswer:",
      temperature=0,
      max_tokens=250,
      frequency_penalty=1,
      presence_penalty=1,
    )
    return response.choices[0].text

def api_fun(question):
    cname = extract_cname(question)
    # print(cname)
    names = [x.strip() for x in cname.split(',')]
    print(names)
    # company_names = get_companies("elasticdb")
    # print(company_names)
    # ax = query_by_company('elasticdb','Alliant', 1)
    # print(ax)
    
    if names[0]:
        clean_data = []
        # snames = get_companies("elasticdb")
        for name in names:
            print(name)
            x = query_question(question, name, 'elasticdb', 2)
            summary = string_convert(x)
            print(summary)
            answer = get_info(summary, question)
            clean_data.append(answer)
            print(clean_data)
            
        # answer = final_prompt(clean_data, question)
        return clean_data
    elif not names[0]:
            company_names = get_companies("elasticdb")
            clean_data = []
            ques = q_general(question)
            print(ques)
            for i in range(len(company_names)):
                if (i+1)%5 == 0:
                    x = query_question(ques, company_names[i], 'elasticdb' , 2)
                    summary = string_convert(x)
                    merg = company_names[i] + ": " + summary
                    answer = get_info(merg, question)
                    clean_data.append(answer)
                    print(clean_data)
                    # clean_data.clear()
                else:
                    x = query_question(ques, company_names[i], 'elasticdb' , 2)
                    summary = string_convert(x)
                    merg = company_names[i] + ": " + summary
                    answer = get_info(merg, question)
                    clean_data.append(answer)
            
    # answer = final_prompt(clean_data, question)
    return clean_data


def retrival(fname):
    print("headings")
    headings(fname)
    print("earnings call")
    text1_data(fname)
    print("Text data")
    text_data(fname)
    if not es_client.indices.exists(index="elasticdb"):
        create_index("elasticdb")
        print("creating index")
    print("refreshing index")
    refresh_index("elasticdb")
    print(fname)
    print("inserting: ",fname)
    index_context(new_sentences, "elasticdb", fname)
    new_sentences.clear()
    headinglist.clear()


def api_fun2(question):
    cname = extract_cname(question)
    # print(cname)
    names = [x.strip() for x in cname.split(',')]
    print(names)
    # company_names = get_companies("elasticdb")
    # print(company_names)
    # ax = query_by_company('elasticdb','Alliant', 1)
    # print(ax)
    
    if names[0]:
        clean_data = []
        # snames = get_companies("elasticdb")
        for name in names:
            print(name)
            x = query_question(question, name, 'elasticdb', 3)
            summary = string_convert(x)
            print(summary)
            answer = get_info2(summary, question, name)
            clean_data.append(answer)
            print(clean_data)
            
        # answer = final_prompt(clean_data, question)
        return clean_data
    elif not names[0]:
            company_names = get_companies("elasticdb")
            clean_data = []
            ques = q_general(question)
            print(ques)
            for i in range(len(company_names)):
                if (i+1)%5 == 0:
                    x = query_question(ques, company_names[i], 'elasticdb' , 2)
                    summary = string_convert(x)
                    merg = company_names[i] + ": " + summary
                    answer = get_info2(merg, question)
                    clean_data.append(answer)
                    print(clean_data)
                    # clean_data.clear()
                else:
                    x = query_question(ques, company_names[i], 'elasticdb' , 2)
                    summary = string_convert(x)
                    merg = company_names[i] + ": " + summary
                    answer = get_info2(merg, question)
                    clean_data.append(answer)
            
    # answer = final_prompt(clean_data, question)
    return clean_data