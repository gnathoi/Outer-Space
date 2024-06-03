## Challenge: Spatial Linking of Heterogenous Data
## Champions: Anne Göbels, Oliver Schulz
## Challenge description

Large amounts of heterogeneous data for existing building assets are often just a conglomeration of paper documents and/or files. While humans can often establish spatial relationships between documents, the amount of data is often too large to keep an overview, and there is still a lack of standardised meta-descriptions to formalise these spatial relationships between them. Although spatial relationships can be established within software applications, these are then locked in data silos. Additionally, the spatial relations are often fuzzy and cannot be precisely defined. 
To enable spatial querying of this data, a meta-schema (i.e., vendor-neutral, outside of specific software) must first be developed. 
- bspw. extension of ICDD schema?

Two main approaches could be considered:

1. Utilising mathematical descriptions such as vectors, matrices, etc., to enable precise positional descriptions. The advantage would be precise positioning, but it may not be intuitive to use for humans.
    
2. Utilising natural language. This approach would be more intuitive and easier to understand but may not be as precise as the mathematical approach. However, it may deal better with the fuzziness. 

## Objective

The aim of this challenge is to devise a scheme for describing spatial relationships between heterogeneous files and its prototypical implementation using the provided data set. It is not specified whether the approach should be mathematical or derived from natural language. The aim is not to develop a new ontology but to use existing concepts as far as possible and implement new axioms ‘dummy-like’ where necessary.

## Challenge Research question

- What should a metadata schema look like that can reflect spatial relations between files?
- How to deal with fuzzy spatial relations/descriptions?
- Are you able to use the schema to enable spatial queries via SPARQL?
- Optional: Enable spatial queries via approaches other than SPARQL?

## Datasets available
- Plans, Models, and Pictures of an existing bridge
- Coordinated Model in Blender, showing the spatial relations

## References
- Spatial Referencing Methods (mathematical, ontological, linguistic..)
