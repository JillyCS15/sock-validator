import argparse
import pandas as pd

from tqdm import tqdm
from rdflib import Graph, URIRef, Literal, Namespace
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
        for idx in tqdm(range(0, size, 50), desc=f"Collecting values of {prop}"):
            try:
                query = f"""
SELECT ?s ?p ?o
WHERE {{
    VALUES ?s {{{' '.join(data['entity'][idx:idx+50]) }}}
    BIND({prop} AS ?p)
    ?s ?p ?o .
}}
"""
                res = query_sparql(query, sparql_endpoint)
                list_data.append(res)
                
            except:
                print("Something wrong in collecting the data properties")
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
    return data_prop

def construct_data_graph(data, data_prop, entity_class):
    # convert data into data graph
    data_graph = Graph()

    # add default namespaces
    dbo_prefix = Namespace("http://dbpedia.org/ontology/")
    wd_prefix = Namespace("http://www.wikidata.org/entity/")
    data_graph.bind("dbo", dbo_prefix)
    data_graph.bind("wd", wd_prefix)

    # add instance relation for all entities
    # only used for checking with target for a certain class
    # if not, just skip it
    for _, row in data.iterrows():
        s = URIRef(row['entity.value'])
        p = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
        o = URIRef(entity_class)
        data_graph.add((s, p, o))

    # add node-property relation for all entities
    for _, row in data_prop.iterrows():
        s = URIRef(row['s.value'])
        p = URIRef(row['p.value'])
        if row['o.type'] == 'literal':
            if row['o.xml:lang'] == 'not specified':
                o = o = Literal(row['o.value'])
            else:
                o = Literal(row['o.value'], lang=row['o.xml:lang'])
        elif row['o.type'] == 'typed-literal':
            o = Literal(row['o.value'], datatype=row['o.datatype'])
        else:
            o = URIRef(row['o.value'])
        data_graph.add((s, p, o))

    data_graph.serialize(destination="data_graph.ttl", format='turtle')


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(allow_abbrev=False,
                                        description="Arguments for preparing data to be validated")
    required = parser.add_argument_group('required arguments')

    required.add_argument("--query_file", type=str, required=True,
                            help="A file path for a SPARQL query file in txt format")
    required.add_argument("--sparql_endpoint", type=str, required=True,
                            help="A string of SPARQL endpoint URL")
    required.add_argument("--class_uri", type=str, required=True,
                            help="An URI of target class")
    required.add_argument("--prop_list", type=str, required=True, nargs="+",
                            help="A list of properties to be checked for each entity")

    args = parser.parse_args()
    filename = args.query_file
    sparql_endpoint = args.sparql_endpoint
    class_uri = args.class_uri
    prop_list = args.prop_list

    data = retrieve_data(filename, sparql_endpoint)
    data_prop = retrieve_data_prop(data, prop_list, sparql_endpoint)

    # create data graph
    construct_data_graph(data, data_prop, class_uri)
