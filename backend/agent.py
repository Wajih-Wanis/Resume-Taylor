from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from backend.types import Resume, JobDescription
from backend.model import Model
import json
import logging

class AgentState(TypedDict):
    base_resume: Resume
    job_description: JobDescription
    generated_resume: Resume | None
    validation_errors: list[str]
    revision_steps: list[str]
    ats_score: float

def _validate_ats_compliance(state: AgentState) -> dict:
    """Node: Validate ATS compliance using known criteria"""
    errors = []
    resume = state["generated_resume"]
    
    # ATS validation rules
    if not resume.profile:
        errors.append("Missing summary/profile section")
    if len(resume.skills or []) < 5:
        errors.append("Insufficient skills listed")
    if not resume.experience:
        errors.append("Missing work experience section")
    
    return {"validation_errors": errors}

def _generate_initial_version(state: AgentState, model: Model) -> dict:
    """Node: Generate initial resume version"""
    prompt = f"""
    Generate initial ATS-optimized resume based on:
    Base Resume: {state['base_resume'].json()}
    Job Description: {state['job_description'].json()}
    
    Requirements:
    - Use standard ATS headers: Summary, Experience, Skills, Education
    - Mirror job description keywords
    - Quantify achievements
    - Use active verbs
    """
    
    response = model._run(prompt)
    try:
        resume_dict = json.loads(response)
        return {"generated_resume": Resume(**resume_dict)}
    except Exception as e:
        logging.error(f"Generation error: {e}")
        return {"validation_errors": [f"Generation failed: {str(e)}"]}

def _analyze_job_alignment(state: AgentState, model: Model) -> dict:
    """Node: Check job requirement alignment"""
    prompt = f"""
    Analyze alignment between generated resume and job requirements:
    
    Resume: {state['generated_resume'].json()}
    Job Description: {state['job_description'].json()}
    
    Identify:
    1. Missing required skills
    2. Under-quantified experiences
    3. Keyword mismatches
    4. Section priority issues
    """
    
    analysis = model._run(prompt)
    return {"revision_steps": [analysis]}

def _self_correct(state: AgentState, model: Model) -> dict:
    """Node: Perform self-correction based on errors"""
    prompt = f"""
    Correct the resume based on these issues:
    {state['validation_errors']}
    {state['revision_steps']}
    
    Current resume:
    {state['generated_resume'].json()}
    
    Maintain:
    - Original factual accuracy
    - ATS-friendly format
    - Job keyword alignment
    """
    
    response = model._run(prompt)
    try:
        resume_dict = json.loads(response)
        return {"generated_resume": Resume(**resume_dict)}
    except Exception as e:
        logging.error(f"Correction error: {e}")
        return {"validation_errors": [f"Correction failed: {str(e)}"]}

def _should_revise(state: AgentState) -> str:
    """Edge: Decide if another revision is needed"""
    if len(state["validation_errors"]) > 0 or len(state["revision_steps"]) > 0:
        return "revise"
    return "end"

def create_resume_agent(model: Model) -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Define nodes
    workflow.add_node("generate_initial", _generate_initial_version)
    workflow.add_node("validate_ats", _validate_ats_compliance)
    workflow.add_node("analyze_alignment", _analyze_job_alignment)
    workflow.add_node("self_correct", _self_correct)
    
    # Define edges
    workflow.set_entry_point("generate_initial")
    
    workflow.add_edge("generate_initial", "validate_ats")
    workflow.add_edge("validate_ats", "analyze_alignment")
    workflow.add_conditional_edges(
        "analyze_alignment",
        _should_revise,
        {
            "revise": "self_correct",
            "end": END
        }
    )
    workflow.add_edge("self_correct", "validate_ats")
    
    return workflow

class EnhancedResumeGenerator:
    def __init__(self, model: Model):
        self.agent = create_resume_agent(model)
        self.model = model
    
    def generate_ats_resume(self, base_resume: Resume, job_desc: JobDescription) -> Resume:
        """Execute the agentic workflow"""
        initial_state = AgentState(
            base_resume=base_resume,
            job_description=job_desc,
            generated_resume=None,
            validation_errors=[],
            revision_steps=[],
            ats_score=0.0
        )
        
        # Execute the graph
        for step in self.agent.stream(initial_state):
            # Add logging/error handling here
            logging.info(f"Agent step: {step}")
        
        return step["generated_resume"]