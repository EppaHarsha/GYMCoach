from services.config.workout_config import PROMPT

class LLMCoach:
    
    def __init__(self,openAI_client):
        
        self.client = openAI_client
        
        self.history=[]
        
        self.system_prompt=PROMPT
        
    def give_feedback(self,event,issue):
        prompt = f"Event:{event}"
        
        if issue:
            prompt+=f"form Issue : {issue}"
        inputs=[
            {"role":"developer","content":self.system_prompt},
            *self.history[-10:],
            {"role":"user","content":prompt}
        ]
        response = self.client.responses.create(
        model="gpt-5.5",
        reasoning={"effort": "low"},
        input=inputs
        )
        text=response.output_text
        
        self.history.append({"role":"assistant","content":text})
        
        return text