import sys
import argparse

import pandas as pd

from tqdm import tqdm
from SPARQLWrapper import SPARQLWrapper, JSON


prefixes = """
@prefix : <http://example.org/ns#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix dbc: <http://dbpedia.org/resource/Category:> .
@prefix dbo: <http://dbpedia.org/ontology/> .
@prefix dbp: <http://dbpedia.org/property/> .
@prefix dbr: <http://dbpedia.org/resource/> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix ex: <http://example.org/ns#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix geo: <http://www.opengis.net/ont/geosparql#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix person: <http://dbpedia.org/ontology/Person> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sock: <https://cs.ui.ac.id/ns/sock#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
"""


def construct_node_shape(node_shape_name, target, is_class_target=True):
    """
    Construct the node shape.

    Parameters
    ----------
    node_shape_name : str
        A name for a node shape
    target : str
        An IRI as a target of node shape 
    is_class_target : bool, optional
        A boolean value to determine the use of target class or target node (default is True)

    Returns
    -------
    str
        A node shape in a type of string
    """

    if is_class_target:
        return f"""
ex:{node_shape_name}
    a sh:NodeShape ;
    sh:targetClass {target} ;
    """
    return f"""
ex:{node_shape_name}
    a sh:NodeShape ;
    sh:targetNode {target} ;
    """


def construct_property_shape(df, prop_col, card_col):
    """
    Construct the property shape.

    Parameters
    ----------
    df : DataFrame
        A name for a node shape
    prop_col : str
        A column name of a property 
    card_col : str
        A column name of a property's cardinality

    Returns
    -------
    str
        A property shape in a type of string
    """

    property_shape = ""

    for _, row in df.iterrows():
        shape = f"""
    sh:property [ a sh:PropertyShape;
        sh:path <{row[prop_col]}>;
        sh:minCount {row[card_col]} ];
"""
        property_shape += shape[1:]

    # correct the last symbol
    property_shape = property_shape[:-2] + '.'

    return property_shape


def construct_shapes_graph(node_shape_name, df, prop_col, card_col, target, is_class_target=True):
    """
    Construct the property shape.

    Parameters
    ----------
    node_shape_name : str
        A name for a node shape
    df : DataFrame
        A name for a node shape
    prop_col : str
        A column name of a property 
    card_col : str
        A column name of a property's cardinality
    target : str
        An IRI as a target of node shape 
    is_class_target : bool, optional
        A boolean value to determine the use of target class or target node (default is True)

    Returns
    -------
    str
        A shapes shape in a type of string
    """

    # create node shape
    node_shape = construct_node_shape(node_shape_name, target, is_class_target)

    # create property shape
    property_shape = construct_property_shape(df, prop_col, card_col)

    # merge property shape with node shape
    shapes_graph = prefixes[1:] + node_shape[:-1] + property_shape[1:]

    return shapes_graph


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


def get_property_by_ontology(class_uri, sparql_endpoint):
    """
    Get all the desired properties of a class by an ontological approach.

    Parameters
    ----------
    class_name : str
        A name of a class 

    Returns
    -------
    DataFrame
        A table consisting of the desired properties
    """

    query = f"""
SELECT DISTINCT ?prop
WHERE {{
    ?prop rdfs:domain {class_uri} .
}}
    """

    # generate data for the shape
    prop_df = query_sparql(query, sparql_endpoint)
    prop_df['cardinality'] = 1

    return prop_df


def get_property_by_statistics(class_uri, sparql_endpoint):
    """
    Get all the desired properties of a class by an statistical approach.

    Parameters
    ----------
    class_name : str
        A name of a class 

    Returns
    -------
    DataFrame
        A table consisting of the desired properties
    """

    # get candidate properties
    print("Get all the candidate properties...")
    query = f"""
SELECT DISTINCT ?prop
WHERE {{
   ?s a {class_uri} ;
        ?prop [] .
    FILTER(isUri(?prop) && STRSTARTS(STR(?prop), STR(dbo:)))
}}
"""
    candidate_prop = query_sparql(query, sparql_endpoint)


    # get number of entities of a class
    query = f"""
SELECT (COUNT(DISTINCT ?entity) AS ?numOfEntities)
WHERE {{
  ?entity a {class_uri} .
}}
"""
    num_of_entities = int(query_sparql(query, sparql_endpoint).iloc[0,2])


    # query the frequency of all the properties
    print("Calculate the relative frequency of each property...")
    list_rel_freq = []

    for idx in tqdm(range(candidate_prop.shape[0]), desc="Calculate the relative frequency of all properties: "):
        prop = candidate_prop.at[idx, 'prop.value']

        query = f"""
SELECT (COUNT(DISTINCT ?entity) AS ?numOfEntities)
WHERE {{
  ?entity a {class_uri} ;
          <{ prop }> [] .
}}
"""

        # count the relative frequency
        num_of_union = int(query_sparql(query, sparql_endpoint).iloc[0,2])
        list_rel_freq.append(num_of_union / num_of_entities)    

    # arrange the result
    prop = candidate_prop.copy()
    prop['rel_freq'] = list_rel_freq
    prop['cardinality'] = 1
    prop.sort_values('rel_freq', ascending=False, inplace=True)
    prop.reset_index(drop=True, inplace=True)

    return prop.head(10)


def generate_by_spreadsheet(data, shape_name_col, shape_target_col, prop, card_col):
    shapes_graph = ""
    for idx in tqdm(range(data.shape[0]), desc="Creating shapes graph: "):
        shape_name = data.at[idx, shape_name_col]
        shape_target = data.at[idx, shape_target_col]
        cardinality = data.at[idx, card_col]

        shapes_graph += \
f"""
ex:{shape_name}Shape a sh:NodeShape ;
    sh:targetNode {shape_target} ;
    sh:property ex:{shape_name}PropertyShape .

ex:{shape_name}PropertyShape a sh:PropertyShape ;
    sh:path {prop} ;
    sh:minCount {cardinality} .
"""

    return prefixes[1:] + shapes_graph


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='commands')

    # A spreadsheet command
    spreadsheet_parser = subparsers.add_parser('spreadsheet', help='Spreadsheet arguments')
    spreadsheet_parser = spreadsheet_parser.add_argument_group('required arguments')
    spreadsheet_parser.add_argument("--file", type=str, required=True,
                            help="A file path for a shapes data file in csv format")
    spreadsheet_parser.add_argument("--shape_name_col", type=str, required=True,
                            help="A column for the name of the shapes, i.e. the title of each entity and contains no whitespaces")
    spreadsheet_parser.add_argument("--shape_target_col", type=str, required=True,
                            help="A column for the shapes' target, i.e. URI of each entity and contains no whitespaces")
    spreadsheet_parser.add_argument("--prop_uri", type=str, required=True,
                            help="An URI coressponding to the path to be checked")
    spreadsheet_parser.add_argument("--card_col", type=str, required=True,
                            help="A column name that contains information regarding the minimum number of paths if considered complete and contains no whitespaces")

    # A ontology command
    ontology_parser = subparsers.add_parser('ontology', help='Spreadsheet arguments')
    ontology_parser = ontology_parser.add_argument_group('required arguments')
    ontology_parser.add_argument("--class_uri", type=str, required=True,
                            help="An URI of a target class for shapes graph")
    ontology_parser.add_argument("--sparql_endpoint", type=str, required=True,
                            help="A string of SPARQL endpoint URL")

    # A statistics command
    statistics_parser = subparsers.add_parser('statistics', help='Spreadsheet arguments')
    statistics_parser = statistics_parser.add_argument_group('required arguments')
    statistics_parser.add_argument("--class_uri", type=str, required=True,
                            help="An URI of a target class for shapes graph")
    statistics_parser.add_argument("--sparql_endpoint", type=str, required=True,
                            help="A string of SPARQL endpoint URL")

    args = parser.parse_args()

    if sys.argv[1] == "spreadsheet":
        filename = args.file
        shape_name = args.shape_name
        shape_target = args.shape_target
        prop = args.prop_uri
        card_col = args.card_col
        
        df = pd.read_csv(filename)
        shapes_graph = generate_by_spreadsheet(df, shape_name, shape_target, prop, card_col)

        with open("shacl-shapes.ttl", "w") as file:
            file.write(shapes_graph)

        print("Successfully created a shapes graph")

    elif sys.argv[1] == 'ontology':
        class_uri = args.class_uri
        shape_name = "".join(class_uri.split(":")[1:])
        sparql_endpoint = args.sparql_endpoint

        # get all the required properties
        print("Get all the required properties...")
        prop = get_property_by_ontology(class_uri, sparql_endpoint)
        print("Succesfully get all the properties")

        # create property shape
        print("Construct a shape graph...")
        shapes_graph = construct_shapes_graph(f"{shape_name}SchemaShapes", 
                                                prop, 
                                                'prop.value', 
                                                'cardinality', 
                                                class_uri)
        with open("shacl-shapes.ttl", "w") as file:
            file.write(shapes_graph)

        print("Successfully created a shapes graph")

    elif sys.argv[1] == 'statistics':
        class_uri = args.class_uri
        shape_name = "".join(class_uri.split(":")[1:])
        sparql_endpoint = args.sparql_endpoint

        # get all the required properties
        print("Get all the required properties...")
        prop = get_property_by_statistics(class_uri, sparql_endpoint)
        print("Succesfully get all the properties")

        # create property shape
        print("Construct a shape graph...")
        shapes_graph = construct_shapes_graph(f"{shape_name}SchemaShapes", 
                                                prop, 
                                                'prop.value', 
                                                'cardinality', 
                                                class_uri)
        with open("shacl-shapes.ttl", "w") as file:
            file.write(shapes_graph)

    else:
        print("A type of argument not acceptible. Try again!")
