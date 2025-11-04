"""
Knowledge Plugin for Semantic Kernel
This plugin provides functions to answer questions about your Databricks Environment.
"""

import os
import json
import time
import requests
from semantic_kernel.functions import kernel_function


class KnowledgePlugin:
    """
    A plugin that provides knowledge about your Databricks Environment.
    """
    
    def __init__(self):
        """Initialize the plugin with configuration from environment variables"""
        self.token = os.getenv("DATABRICKS_TOKEN")
        self.databricks_host = os.getenv("DATABRICKS_HOST")
        self.genie_space_id = os.getenv("GENIE_SPACE_ID")
        
        if not self.token:
            raise ValueError("DATABRICKS_TOKEN not found in environment variables")
        if not self.databricks_host:
            raise ValueError("DATABRICKS_HOST not found in environment variables")
        if not self.genie_space_id:
            raise ValueError("GENIE_SPACE_ID not found in environment variables")

    def post_genie(self, genie_space_id: str, prompt: str) -> dict:
        headers = {
          "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.databricks_host}/api/2.0/genie/spaces/{genie_space_id}/start-conversation"

        response = requests.post(url, headers=headers, json={"content": prompt})
        return response  
 
    def get_genie_query_results(self, genie_space_id: str, conversation_id: str, message_id: str) -> dict:
        
        headers = {
          "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.databricks_host}/api/2.0/genie/spaces/{genie_space_id}/conversations/{conversation_id}/messages/{message_id}"

        response = requests.get(url, headers=headers)
  
        return response.json()  

    def get_genie_query_attachment_results(self, genie_space_id: str, conversation_id: str, message_id: str, attachment_id: str) -> list:
        
        headers = {
          "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.databricks_host}/api/2.0/genie/spaces/{genie_space_id}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/query-result"

        response = requests.get(url, headers=headers)
        return response.json()['statement_response']['result']['data_array']
    
    def _format_query_results(self, data_array: list) -> str:
        """
        Format query results (array of arrays) into a readable table string.
        
        Args:
            data_array: Array of arrays where first row is headers, rest are data
            
        Returns:
            Formatted table string
        """
        if not data_array or len(data_array) == 0:
            return "No results returned."
        
        # First row is typically headers
        if len(data_array) == 1:
            # Only headers, no data
            return f"Columns: {', '.join(str(col) for col in data_array[0])}\n\nNo data rows returned."
        
        headers = data_array[0]
        rows = data_array[1:]
        
        # Calculate column widths
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Build table string
        result_lines = []
        
        # Header row
        header_line = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
        result_lines.append(header_line)
        
        # Separator
        separator = "-+-".join("-" * w for w in col_widths)
        result_lines.append(separator)
        
        # Data rows (limit to 50 rows to avoid overwhelming output)
        max_rows = 50
        for i, row in enumerate(rows[:max_rows]):
            row_line = " | ".join(str(cell).ljust(col_widths[j]) for j, cell in enumerate(row))
            result_lines.append(row_line)
        
        if len(rows) > max_rows:
            result_lines.append(f"\n... and {len(rows) - max_rows} more rows")
        
        result_lines.append(f"\nTotal rows: {len(rows)}")
        
        return "\n".join(result_lines)

    @kernel_function(
        name="get_databricks_info",
        description="Use this tool to answer questions about Databricks, Unity Catalog, tables, schemas, clusters, jobs, and data. Pass the user's natural language question directly - DO NOT convert to SQL. Genie will handle query generation internally."
    )
    def get_databricks_info(self, query: str, wait_seconds: int = 5, max_retries: int =  20) -> str:
        """
        Get information from Databricks Genie about the Databricks environment.
        This function accepts natural language questions and passes them directly to Genie.
        
        Args:
            query: Natural language question about Databricks (DO NOT pass SQL, pass the question as-is)
            wait_seconds: Seconds to wait between status checks
            max_retries: Maximum number of retries before giving up
            
        Returns:
            The response from Genie
        """
        genie_space_id = self.genie_space_id
        response = self.post_genie(genie_space_id, query)  

        if response.status_code == 200:  
            try:  
                raw_post_value = json.loads(response.text)  
            except json.JSONDecodeError as exc:  
                return "Genie JSON decode error on POST response:", exc

            conversation_id = raw_post_value.get('conversation_id')  
            message_id = raw_post_value.get('message_id')  
            if not conversation_id or not message_id:  
                return "Genie Missing conversation_id or message_id in the response."

            status = 'IN_PROGRESS'  
            current_try = 0  
            raw_get_value = {}  

            while status != 'COMPLETED' and current_try < max_retries:  
                raw_get_value = self.get_genie_query_results(genie_space_id, conversation_id, message_id)  
                status = raw_get_value.get('status', 'UNKNOWN')  
                current_try += 1  
                if status != 'COMPLETED':  
                    time.sleep(wait_seconds)  

            if status != 'COMPLETED':  
                return f"Genie query did not complete after {max_retries} retries."

            attachments = raw_get_value.get('attachments', [])  
            if not attachments:  
                return "No attachments found in the Genie response."

            attachment_value = attachments[0]  
            attachment_id = attachment_value.get('attachment_id')  
            if not attachment_id:  
                return "No attachment_id found in the first Genie attachment."

            if 'text' in attachment_value:  
                text_content = attachment_value['text'].get('content', '')  
                return text_content

            elif 'query' in attachment_value:  
                query_description = attachment_value['query'].get('description', '')  
                try:  
                    query_results = self.get_genie_query_attachment_results(genie_space_id, conversation_id, message_id, attachment_id)  
                    # Format the array of arrays into a readable table
                    formatted_results = self._format_query_results(query_results)
                    final_value = query_description + "\n\n" + formatted_results
                except Exception as e:  
                    final_value = f"{query_description}\n\nError retrieving results: {str(e)}"
                return final_value
            else:  
                return("Error: Failed to decode Genie results from the attachment.")  
        else:  
            try:  
                error_message = response.json()  
            except Exception:  
                error_message = response.text  
            return f"Error with Genie: {error_message}"

