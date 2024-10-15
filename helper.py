import pandas as pd

def weighted_counts(x):
    # x is a DataFrame of grouped values including the 'wts' column for weights
    total_weight = x['wts'].sum()
    return total_weight

def map_scaled_responses(df,column_name):
    """
    replaces responses in a dataframe column with the version specified in response_mapping
    """
    response_mapping = {
        'Very concerned': 'Concerned',
        'Somewhat concerned': 'Concerned',
        'Not too concerned': 'Not Concerned',
        'Not at all concerned': 'Not Concerned',
        "Don't know/No opinion": "Don't know/No opinion",
        'Very important': 'Important',
        'Somewhat important': 'Important',
        'Not too important': 'Not important',
        'Not at all important': 'Not important',
        "Far too little":"Too little",
        "Far too much":"Too much"        
    }

    # if not df[column_name].str.lower().str.contains("confident").any(): #if Response values don't include "confident"
        # Apply the mapping to collapse response categories
    df[column_name] = df[column_name].map(response_mapping)
    return df

def clean_key(key_name):
    try:
        return key_name.split(' --- ')[1].strip()
    except:
        return key_name
    
def get_name_from_codebook(codebook, question,level):
    return codebook.loc[(codebook["question"] == question) & (codebook["value"] == level), "code"].values[0]
    
def get_percent_select_multiple_base(data,q_codebook,question="BPC1") -> dict:
    """
    Returns the percentage of respondents who selected each option for a given question. 
    """
    weighted_numerator = {}
    weighted_denominator = {}

    # select all columns including question text
    for question_option in data.filter(regex='^'+question+"_").columns:
        # calculate weighted numerator and denominator (aka # of respondents who selected each option)
        weighted_numerator[question_option] = ((data[question_option] == 1) * data['wts']).sum()
        weighted_denominator[question_option] = ((data[question_option] == 1) * data['wts']).sum() + \
                                                ((data[question_option] == 2) * data['wts']).sum()

    # divide numerator by denominator
    weighted = {}
    for key in weighted_numerator.keys():
        if "TEXT" not in key:
            weighted[key] = weighted_numerator[key] / weighted_denominator[key]

    # replace weighted key name with value from 
    weighted = {q_codebook[key]: value for key, value in weighted.items()}

    # clean (remove question text from response category)
    weighted = {clean_key(k): v for k, v in weighted.items()}

    return weighted


def get_percents_select_one_base(data,codebook,question):
    """
    Returns percent of respondents who selected each option for 'select one' questions
    """
    numerators = data.groupby(question).apply(lambda x: x['wts'].sum())
    denominator = numerators.sum()

    results = numerators/denominator

    new_index = []
    for index in results.index:
        new_index.append(get_name_from_codebook(codebook,question,index))

    results.index = new_index
        
    return results

def get_percents(data,codebook,q_codebook,question="BPC1",demo=None) -> dict:
    """
    Returns percent who selected each option,
    works for questions that have multiple or single selection.

    Demo input optional.
    """
    q_columns = data.filter(regex='^'+question+"_").columns

    if len(q_columns) == 0: # underscore only used when each option has selections
        multiple_selections = False

    ## to address single select questions with a short response text answer
    elif (len(q_columns) == 1) and ("TEXT" in q_columns[0]):
        multiple_selections = False

    ## otherwise, probably mulitple selections
    else:
        multiple_selections = True

    demo_results = {}

    #if demo provided
    if demo:
        for demo_group, group_data in data.groupby([demo]):
            #lookup demo name
            demo_category_name = get_name_from_codebook(codebook,demo,demo_group[0])
            #store to results dict
            if multiple_selections:
                demo_results[demo_category_name] = get_percent_select_multiple_base(group_data,q_codebook,question)
            else:
                demo_results[demo_category_name] = get_percents_select_one_base(group_data,codebook,question)

    #either way, add results for overall pop

    if multiple_selections:
        demo_results["overall"] = get_percent_select_multiple_base(data,q_codebook,question)
    else:
        demo_results["overall"] = get_percents_select_one_base(data,codebook,question)

    return pd.DataFrame(demo_results).sort_values(by='overall',ascending=False)