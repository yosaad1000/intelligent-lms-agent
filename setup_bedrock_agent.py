#!/usr/bin/env python3
"""
Setup basic Bedrock Agent for RAG Chat
"""

import boto3
import json
import time

def create_basic_bedrock_agent():
    """Create a basic Bedrock agent for chat functionality"""
    
    bedrock_agent_client = boto3.client('bedrock-agent')
    
    # Basic agent configuration
    agent_name = "lms-chat-agent"
    foundation_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Check if agent already exists
    try:
        agents = bedrock_agent_client.list_agents()
        for agent in agents.get('agentSummaries', []):
            if agent['agentName'] == agent_name:
                agent_id = agent['agentId']
                print(f"✅ Found existing Bedrock Agent: {agent_id}")
                
                # Check for existing alias
                try:
                    aliases = bedrock_agent_client.list_agent_aliases(agentId=agent_id)
                    for alias in aliases.get('agentAliasSummaries', []):
                        if alias['agentAliasName'] == 'prod':
                            alias_id = alias['agentAliasId']
                            print(f"✅ Found existing Agent Alias: {alias_id}")
                            return agent_id, alias_id
                except:
                    pass
                
                # Create alias for existing agent
                try:
                    alias_response = bedrock_agent_client.create_agent_alias(
                        agentId=agent_id,
                        agentAliasName="prod",
                        description="Production alias for LMS chat agent"
                    )
                    alias_id = alias_response['agentAlias']['agentAliasId']
                    print(f"✅ Created Agent Alias: {alias_id}")
                    return agent_id, alias_id
                except Exception as e:
                    print(f"⚠️  Could not create alias: {e}")
                    return agent_id, "TSTALIASID"  # Use test alias
                
    except Exception as e:
        print(f"⚠️  Could not list existing agents: {e}")
    
    agent_instruction = """You are an intelligent educational assistant helping students learn from their uploaded documents. 

Your capabilities:
- Answer questions about uploaded educational materials
- Provide explanations and clarifications
- Help students understand complex concepts
- Reference specific parts of documents when answering

Guidelines:
- Always be helpful and educational
- Cite sources when referencing uploaded documents
- If you don't know something, say so clearly
- Keep responses focused and relevant to the question
- Encourage learning and curiosity"""
    
    try:
        # Create the agent
        response = bedrock_agent_client.create_agent(
            agentName=agent_name,
            foundationModel=foundation_model,
            instruction=agent_instruction,
            description="Educational chat agent for LMS system"
        )
        
        agent_id = response['agent']['agentId']
        print(f"✅ Created Bedrock Agent: {agent_id}")
        
        # Prepare the agent
        print("🔄 Preparing agent...")
        prepare_response = bedrock_agent_client.prepare_agent(agentId=agent_id)
        
        # Wait for agent to be prepared
        print("⏳ Waiting for agent to be prepared...")
        max_wait = 60  # Maximum wait time in seconds
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                agent_status = bedrock_agent_client.get_agent(agentId=agent_id)
                status = agent_status['agent']['agentStatus']
                print(f"   Agent status: {status}")
                
                if status == 'PREPARED':
                    break
                elif status == 'FAILED':
                    raise Exception("Agent preparation failed")
                    
                time.sleep(5)
                wait_time += 5
            except Exception as e:
                print(f"   Error checking agent status: {e}")
                break
        
        # Create agent alias
        alias_response = bedrock_agent_client.create_agent_alias(
            agentId=agent_id,
            agentAliasName="prod",
            description="Production alias for LMS chat agent"
        )
        
        alias_id = alias_response['agentAlias']['agentAliasId']
        print(f"✅ Created Agent Alias: {alias_id}")
        
        return agent_id, alias_id
        
    except Exception as e:
        print(f"❌ Error creating Bedrock agent: {e}")
        return None, None

def update_lambda_environment_variables(agent_id, alias_id):
    """Update Lambda functions with Bedrock agent IDs"""
    
    lambda_client = boto3.client('lambda')
    
    functions_to_update = [
        'lms-chat-function',
        'lms-file-function'
    ]
    
    for function_name in functions_to_update:
        try:
            # Get current environment variables
            response = lambda_client.get_function_configuration(
                FunctionName=function_name
            )
            
            env_vars = response.get('Environment', {}).get('Variables', {})
            
            # Update with Bedrock agent IDs
            env_vars.update({
                'BEDROCK_CHAT_AGENT_ID': agent_id,
                'BEDROCK_AGENT_ALIAS_ID': alias_id,
                'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0',
                'BEDROCK_EMBEDDING_MODEL_ID': 'amazon.titan-embed-text-v1'
            })
            
            # Update function configuration
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': env_vars}
            )
            
            print(f"✅ Updated {function_name} with Bedrock agent configuration")
            
        except Exception as e:
            print(f"❌ Error updating {function_name}: {e}")

def main():
    """Setup Bedrock agent and configure Lambda functions"""
    
    print("🤖 Setting up Bedrock Agent for RAG Chat")
    print("=" * 50)
    
    # Create Bedrock agent
    agent_id, alias_id = create_basic_bedrock_agent()
    
    if agent_id and alias_id:
        print(f"\n📋 Bedrock Agent Configuration:")
        print(f"   Agent ID: {agent_id}")
        print(f"   Alias ID: {alias_id}")
        
        # Update Lambda functions
        print(f"\n🔄 Updating Lambda functions...")
        update_lambda_environment_variables(agent_id, alias_id)
        
        # Update .env file
        print(f"\n📝 Updating .env file...")
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            # Update agent IDs in .env
            env_lines = env_content.split('\n')
            updated_lines = []
            
            for line in env_lines:
                if line.startswith('BEDROCK_CHAT_AGENT_ID='):
                    updated_lines.append(f'BEDROCK_CHAT_AGENT_ID={agent_id}')
                elif line.startswith('BEDROCK_AGENT_ALIAS_ID='):
                    updated_lines.append(f'BEDROCK_AGENT_ALIAS_ID={alias_id}')
                else:
                    updated_lines.append(line)
            
            # Add if not exists
            if not any(line.startswith('BEDROCK_CHAT_AGENT_ID=') for line in env_lines):
                updated_lines.append(f'BEDROCK_CHAT_AGENT_ID={agent_id}')
            if not any(line.startswith('BEDROCK_AGENT_ALIAS_ID=') for line in env_lines):
                updated_lines.append(f'BEDROCK_AGENT_ALIAS_ID={alias_id}')
            
            with open('.env', 'w') as f:
                f.write('\n'.join(updated_lines))
            
            print(f"✅ Updated .env file with agent configuration")
            
        except Exception as e:
            print(f"⚠️  Could not update .env file: {e}")
        
        print(f"\n🎉 Bedrock Agent Setup Complete!")
        print(f"🚀 Your RAG system now has AI capabilities enabled!")
        
    else:
        print(f"\n❌ Failed to create Bedrock agent")

if __name__ == "__main__":
    main()