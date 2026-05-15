# Search returned students in the English and Chinese press

library(histtext)
library(tidyverse)


list_corpora()


# load keyword list 

keywords <- read_delim("Desktop/RS/keywords.csv", delim = ";", escape_double = FALSE, trim_ws = TRUE)

key_en <- keywords %>% filter(language == "English")
key_zh <- keywords %>% filter(language == "Chinese")


## English press

### 4750 docs in Proquest

query_terms_en <- paste0('"', key_en$term, '"', collapse = ", ")

proquest_exp <- search_documents_ex(
  query_terms_en,
  corpus = "proquest")

### concordance (5616 occurrences)

proquest_conc <- search_concordance_ex(
  query_terms_en,
  corpus = "proquest", context_size = 500)

# remove American trained 

# use concordance to verify 

view_document(1324809831, "proquest", query = c("returned student"))

# differences (articles retrieved through the interface but missing in query expansion) 

missing <- proquest %>% filter(!id %in% proquest_exp$DocId) # none
missing <- proquest_exp %>% filter(!DocId %in% proquest$id) # 3491 

# retrieve full text 

proquest_exp_ft <- get_documents(proquest_exp, "proquest")

# check articles 

view_document(1371325045, "proquest", "foreign-trained")
view_document(1754571123, "proquest", "foreign-trained")
view_document(1371519349, "proquest", "educated")

# retrieve article categories  

proquest_meta <- get_search_fields_content(proquest_exp,corpus="proquest", 
                                   search_fields=c(list_search_fields("proquest"),
                                                   list_filter_fields("proquest"))) 


proquest_meta_id <- proquest_meta %>% select(DocId, category) %>% mutate(DocId = as.double(DocId))

# normalize categories

proquest_meta_id <- proquest_meta_id %>% 
  mutate(category = str_replace(category, "\\['","")) %>% 
  mutate(category = str_replace(category, "'\\]",""))  %>% 
  mutate(category = str_replace(category, "', '",", "))

proquest_meta_id %>% group_by(category) %>% count(sort = TRUE)

library(dplyr)
library(stringr)

proquest_meta_id <- proquest_meta_id %>%
  mutate(
    category_clean = case_when(
      
      # Articles / Features
      str_detect(category, "Feature") & str_detect(category, "Article") ~ 
        "Article / Feature",
      
      # Advertisements
      str_detect(category, "Advertisement") & 
        str_detect(category, "Classified Advertisement") ~ 
        "Classified Advertisement",
      
      category == "Advertisement" ~ 
        "Advertisement",
      
      # Editorials / Commentary
      str_detect(category, "Editorial") & 
        str_detect(category, "Commentary") ~ 
        "Editorial / Commentary",
      
      # Letters
      str_detect(category, "Letter to the Editor") & 
        str_detect(category, "Correspondence") ~ 
        "Letter / Correspondence",
      
      # Front matter
      str_detect(category, "Table of Contents") | 
        str_detect(category, "Front Matter") ~ 
        "Front Matter",
      
      # Marriage / Obituary notices
      str_detect(category, "Marriage Announcement") | 
        str_detect(category, "Obituary") ~ 
        "Personal Notices",
      
      # Keep remaining categories
      TRUE ~ category
    )
  )

proquest_meta_id %>% group_by(category_clean) %>% count(sort = TRUE)

# South China Morning Post (SCMP) post 1949

scmp_exp <- search_documents_ex(
  query_terms_en,
  corpus = "scmp-recent") # 2786

scmp_conc <- search_concordance_ex(
  query_terms_en,
  corpus = "scmp-recent", context_size = 500) # 3067

scmp_exp_ft <- get_documents(scmp_exp,
  corpus = "scmp-recent")

## Chinese pres

###  docs in Shenbao

query_terms_zh <- paste0('"', key_zh$term, '"', collapse = ", ")

shenbao_exp <- search_documents_ex(
  query_terms_zh,
  corpus = "shunpao-revised")

### concordance (occurrences)

shenbao_conc <- search_concordance_ex(
  query_terms_zh,
  corpus = "shunpao-revised", 
  context_size = 100)

shenbao_exp_ft <- get_documents(shenbao_exp, "shunpao-revised")

# save datasets 

write.csv(shenbao_conc, "~/data/shenbao_conc.csv")
write.csv(proquest_conc, "~/data/proquest_conc.csv")
write.csv(scmp_conc, "~/data/scmp_conc.csv")
write.csv(shenbao_exp_ft, "~/data/shenbao_exp_ft.csv")
write.csv(proquest_exp_ft, "~/data/proquest_exp_ft.csv")
write.csv(scmp_exp_ft, "~/data/scmp_exp_ft.csv")


