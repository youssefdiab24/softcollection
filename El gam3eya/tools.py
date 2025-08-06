tool = {
    "name": "store_feedback",
    "description": "The tool stores and update at every message the call reaches for it to summarize the call at the end",
    "parameters": {
        "type": "object",
        "properties": {
            "milestone": {
                "type": "string",
                "description": "Call update, like 'قال إنه سيدفع الأسبوع القادم'"
            }
        },
        "required": ["milestone"]
    }
}


#dynamic feedback
#store each milestone in the call (append to array -> .txt)
#customer responded, when, how, refused, 
#this tool is dynamically called to update the milestones reached in the call which then will be acculmated to form call summary
#update_text : this is after we reach a milestone 
#model -> full summary


#the update is responded, extract arg , append array , combine, add to sheets

