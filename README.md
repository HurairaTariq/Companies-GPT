Executive Summary:
This project was a based on question and answer system in which we have to feed data first and
after that we need to get answers related to our query accordingly with a high accuracy rate.
Project Plan:
We divided the whole project into 6 modules:
1. Data Extraction.
2. Data Insertion.
3. Data retrieval from db.
4. Single file.
5. Multiple files.
6. All files.
Project Status Summary:
Data Extraction: 
In data extraction we are extracting the meaningful data from the files. We are getting earnings
call, paragraph names by which we are getting its text data.
Data Insertion: 
In this we create an index with the name if “elasticdb” if and only if it doesn’t exists. After that
we refreshes the index.
After we done that we are going to insert our data into the elastic search db. And we are doing
that so, by getting the data, and making chunks of 7 lines. And then we insert the data into the
elastic search. Which vectorize the data and saves it along with the score.
Data retrieval from db: 
This module the retrieval of data works with the last 3 modules. Its information will be given in
those modules.
Single And Multiple files: 
The first and the second module works on the question in which single and multiple files are
targeted.

• Like if the question is being asked from one or more files (with name of companies) a
prompt will extract the names of the companies from the question.

• And after that we will send our question to the elastic search which will give the most
similar data according to our question. (gives top 3 similar chunks).

• And then we will send our question along with the company name to a prompt which will
extract the exact answer from the data. And this will be applied in all the company names
given in the question.

• Now all the company answers will be given to a final prompt which beautifies the give
data according to an answer.

All Files: 
And the comes a scenario where there is no company name given in the question and for
that we have to do:

• For these type of questions we have to search and get the data from all tha
companies given. 
• So for that we extract all the company names from the elastic search db. 
• And we get the data (gives top 3 similar chunks). the elastic search db according to
the question and all the companies one by one. 
• And each companies data, name along with the question is given to a prompt which
gives us the relatable data for that question. 
• If that’s done we then give that data to a final prompt which beautifies the give data
according to an answer. 

Endpoints: 
• Health Check.

• Question Answering.

• Feeding Data.

• Feeding Data1.

• Delete

• Delete2

Note: 
• Data insertion in the elastic search db takes a lot of time because of the vectorization of 
the data. And due to that on server it gives us a critical timeout error during the 
insertion. 
• On the first index of the txt file there must be the name of the company. 
 
Samples: 
"question": 
"Who is hosting the conference call for Amgen's and Alliant Energy's Q3 2022
financial results"
"Answer": 
" Jason is hosting the conference call for Amgen's Q3 2022 financial results and Susan
Gille is hosting the conference call for Alliant Energy's Q3 2022 financial results."
'question": 
"What is the main focus of Amgen as a company compared to what was announced
in Alliant Energy's news release for Q3 2022 earnings?"
"Answer": " 
The drivers of future earnings growth for AvalonBay Communities are the
development projects underway, further margin improvement from operating model initiatives,
return on structured investment program and an earn-in above traditional levels."
"question": 
"give me the names who's hosting the conference call in all companies?"
"Answer": 
"Yan Jin (Eaton Corp plc), Fabrizio Freda and Tracey Travis (CBRE Group, Inc.), Susan
Gille and Maxius Mezz (AMGEN INC), Mike Salvino and Ken Sharp (DXC Technology Co.), Tom and
Jessica Hansen (D.R. Horton Inc.), Jason Reilley (AvalonBay Communities) David Straube (EPAM
Systems) and Marius Merz (BNY Mellon)

