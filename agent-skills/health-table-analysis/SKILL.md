---
{"id":"health-table-analysis","version":"1.0.0","description":"Plan cautious analysis of health encounter tables.","when_to_use":["health","diabetes","diabetic","patient","readmission","readmitted","patient_nbr"],"operations":["inspect_csv"],"data_classes":["metadata","data_card","aggregates"],"family":"table-analysis","specificity":1}
---
First establish encounter versus patient grain from supplied definitions. Check repeated patient identifiers and missing-code meanings. Unless asked otherwise, propose one concise descriptive question using actual fields and an explicit denominator. Age bands and category codes are not measurements. Inferential work needs suitable variables and justified repeated-observation handling. Do not infer clinical meanings or causality.
