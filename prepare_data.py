import time
import sys
import pandas as pd

from SPARQLWrapper import SPARQLWrapper, JSON

def query_sparql(query, sparql_endpoint):
  """
  Query to certain SPARQL endpoint, such as Wikidata SPARQL.

  Parameters
  ----------
  query : str
    A SPARQL query to be run
  sparql_endpoint : str
    A SPARQL API endpoint 

  Returns
  -------
  DataFrame
    A table consisting of instances to be validated
  """

  # set up the query
  sparqlwd = SPARQLWrapper(sparql_endpoint)
  sparqlwd.setQuery(query)
  sparqlwd.setReturnFormat(JSON)

  # get the data and transform the result into pandas dataframe
  while True:
    try:
      results = sparqlwd.query().convert()
      results_df = pd.json_normalize(results['results']['bindings'])
      break
    except:
      continue
  
  # return the result in dataframe
  return results_df

def get_data_prop(df, prop_list, sparql_endpoint):
    """
    Query the property value given all the instances to be validated.

    Parameters
    ----------
    df : DataFrame
        A table containing all the instances to be validated
    prop_list : list
        A list of properties to be checked
    window_size : int
        A number of data instances used in one query
    sparql_endpoint : str
        A SPARQL API endpoint 

    Returns
    -------
    DataFrame
        A table consisting of all the properties of instances along with their values
    """

    # initiate the variables
    size = df.shape[0]
    list_data = []

    for prop in prop_list:
        # initiate index
        idx_lower = 0
        idx_upper = 50

        # window-looping through length of data
        while idx_lower <= size:
            if idx_upper > size:
                idx_upper = size
            
            # check the index
            print(idx_lower, idx_upper)

            while True:
                try:
                    query = f"""
SELECT ?s ?p ?o
WHERE {{
    VALUES ?s {{{' '.join(data['entity'][idx_lower:idx_upper]) }}}
    BIND({prop} AS ?p)
    ?s ?p ?o .
}}
"""
                    res = query_sparql(query, sparql_endpoint)
                    list_data.append(res)

                except:
                    time.sleep(5)
                    continue

                # update idx
                idx_lower += 50
                idx_upper += 50

                break

    return pd.concat(list_data, ignore_index=True, sort=False)

def retrieve_data(filename, sparql_endpoint):
    with open(filename, 'r') as file:
        query = file.read()

    print("Retrieving data ...")
    data = query_sparql(query, sparql_endpoint)
    data['entity'] = data['entity.value'].apply(lambda x: f"<{x}>")
    data.to_csv("data.csv")
    print("Succesfully retrieve data")
    return data

def retrieve_data_prop(data, prop_list, sparql_endpoint):
    print("Retrieving properties of data ...")
    data_prop = get_data_prop(data, prop_list, sparql_endpoint)
    data_prop.to_csv('data_prop.csv')
    print("Succesfully retrieve data properties")

if __name__ == "__main__": 
    filename = sys.argv[1]
    sparql_endpoint = sys.argv[2]
    prop_list = sys.argv[3].split(',')

    data = retrieve_data(filename, sparql_endpoint)
    data_prop = retrieve_data_prop(data, prop_list, sparql_endpoint)


