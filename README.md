# Table of Content

# Table of Contents
1. [Overview](#overview)
2. [Motivation](#motivation)
3. [Functions](#functions)
4. [How to Setup](#how-to-setup)
5. [Code Example](#code-example)

<br />
<br />

# Overview

<p align="center">
    <img src="./readme-images/logo.jpg" alt="drawing" width="75%"/>
</p>

SoCK Library is a library developed with Python programming. This library contains functions that can be used in the process of validating the completeness of the knowledge graph data. The functions available in this library are data collection, shape formation, data validation, and data visualization. Users are expected to be familiar with using Python to use this library properly.

>The SoCK library reuses some of the existing Python libraries as **requirements**, such as:
>- [RDFLib](https://rdflib.readthedocs.io/)
>- [SPARQLWrapper](https://sparqlwrapper.readthedocs.io/)
>- [PySHACL](https://pypi.org/project/pyshacl/)
>- [Pandas](https://pandas.pydata.org/)
>- [Plotly](https://plotly.com/python/)

# Motivation

SoCK Validator is part of the SoCK Framework project. This project exists because of the rapid development of knowledge graphs. However, it is not supported by a good data quality, especially in terms of completeness. Therefore, the SoCK framework was developed as a pattern-oriented framework to support the creation and validation of knowledge about completeness in KGs. All the developed patterns and their instantiations can be accessed [here](https://sock.cs.ui.ac.id). Happy exploring!

# Functions

SoCK library provides several functions to perform completeness pattern instatiation and completeness validation.

- ```query_sparql```, performs query on a SPARQL endpoint.
- ```get_data_prop```, gets all the required properties for a validation process.
- ```construct_node_shape```, build a node shape.
- ```construct_property_shape```, build a property shape.
- ```construct_shapes_graph```, merge a node shape and a property shape to be a shapes graph as an instance of completeness pattern.
- ```build_data_graph```, constructs a data graph from all the collected data.
- ```validate_graph```, performs a SHACL validation based on a data graph and a shapes graph.
- ```create_report_validation```, converts validation report from a graph to a form of table.
- ```create_completeness_info_viz```, generates a visualization from table of validation report.

All the functions above are generally used consecutively. We prepare a demo to use this library with all thos functions on [this section](#code-example).

# How to Setup

1. The user prepares a Python file.
2. The user is looking for the required function.
3. The user copies the function to be used and pastes it in the prepared file.

# Code Example

Given a use case to check each instance of class ```dbo:Country``` in DBpedia has a label and description property. Then, we find out ```rdfs:label``` is a label property and ```rdfs:comment``` is a description property they used.

1. First of all, we have to prepare a Python file to run all the codes. I recommend to use a Python Notebook file.

2. Create an instance of a completeness pattern from [here](https://sock.cs.ui.ac.id/pattern/). Based on the use case, we choose a label and description completeness pattern. Here is the instantiation of its pattern using a manual approach.
    ```
    # prefixes

    ex:CountryShape
    a sh:NodeShape;
    sh:targetClass %% CLASS %%;
    sh:property [ a sh:PropertyShape;
        sh:path rdfs:label;
        sh:minCount 1 ];
    sh:property [ a sh:PropertyShape;
        sh:path rdfs:comment;
        sh:minCount 1 ].
    ```

3. That instance is used to validate the knowledge graph data. So, now we have to get the data using the code below. Here we limit the result up to 1000 first data.
    ```python
    # get all data to be validated
    query = """
    SELECT DISTINCT ?entity
    WHERE {
        ?entity a dbo:Country .
    }
    LIMIT 1000
    """

    data = query_sparql(query, "http://dbpedia.org/sparql")


    # get all the property values
    data['entity'] = data['entity.value'].apply(lambda x: f"<{x}>")

    dbpedia_endpoint = "http://dbpedia.org/sparql"
    prop_list = ['rdfs:label', 'rdfs:comment']

    data_prop = get_data_prop(data, prop_list, 50, dbpedia_endpoint)
    ```

4. After we get all the data, we have to build a data graph and a shapes graph. Let's say that the pattern instance we use is saved on ```./LDC-Country.ttl```.
    ```python
    # build data graph
    data_graph = build_data_graph(data, data_prop)

    # build shapes graph from the instantiation
    shapes_graph = build_shapes_graph("./LDC-Country.ttl")
    ```

5. Having the data graph and shapes graph, We are ready to run a validation process as a code written below.
    ```python
    conforms, report_graph, report_text = validate_graph(shapes_graph, data_graph)
    ```

6. Then, we create a validation report in a form of table. We use ```create_report_validation``` to convert a validation report from a graph to a table form.
    ```python
    prop_list = ['rdfs:label', 'rdfs:comment']

    validation = create_report_validation(data, "entity.value", report_graph, prop_list)
    ```

7. Lastly, we visualize the report to simplify the analysis and understanding process.
    ```python
    create_completeness_info_viz(
        validation,
        prop_list,
        'Label and Description Completeness Validation of ...')
    ```
    <p align="center">
        <img src="./readme-images/ldc-country.png" alt="drawing" width="75%"/>
    </p>
