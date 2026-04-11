import pandas as pd
import json
import ast
import re
import os

def extract_json(text):
  match = re.search(r"```json(.*?)```", text, re.DOTALL)
  if match:
    return match.group(1).strip()
  else:
    return None

def clean_bold(text):
  return re.sub(r"\*\*(.*?)\*\*", r"\1", text)

def clean_header(text):
  clean_text = re.sub(r'^##+ .*$', '', text, flags=re.MULTILINE)
  clean_text = re.sub(r'^--+$', '', clean_text, flags=re.MULTILINE)
  return clean_text

def delete_comments(json_text):
  """
  There are a few annotations (values of the "formulations" key of the dictionary) that contain comments of the format: // or /* */, which make `json.loads` fail.
  This function aims to fix them.
  """
  json_text = re.sub(r'//.*', '', json_text)
  json_text = re.sub(r'/\*.*?(:?\*/|\n)', '', json_text, flags=re.DOTALL)
  return json_text

def fix_multiline_strings(json_text):
  """
  There are a few CRs (values of the "CR" key of the dictionary) that contain new lines in bad formats, which make `json.loads` fail.
  This function aims to fix them.
  """
  def replacer(match):
    content = match.group(1)
    content = (content
               .replace('"', '\"')
               .replace('\\"', '\"')
               .replace("\n", "\\n")
               .replace("\t", "\\t")) # Added tab escaping
    formulation_wording = match.group(2)
    return f'"CR": "{content}"{formulation_wording}'

  fixed = re.sub(r'"CR":\s*"(.*?)"(,\s*"formulations")', replacer, json_text, flags=re.DOTALL)
  return fixed

def extract_generations_annotations(json_string_input):
  # The input 'json_string_input' is assumed to be the raw JSON string from 'crh' column.
  # The extract_json function is not needed here as the data is already raw JSON.

  if not isinstance(json_string_input, str):
    return (None, None, None)

  # Apply fixes for multiline strings and comments
  fixed_multiline_string = fix_multiline_strings(json_string_input)
  no_comments_string = delete_comments(fixed_multiline_string)

  try:
    response_dict = json.loads(no_comments_string)
  except json.JSONDecodeError:
    return (None, None, None)

  if isinstance(response_dict, dict):
    if ("CR" in response_dict) and ("formulations" in response_dict):
      if isinstance(response_dict["formulations"], dict):
        if ("diagnostics" in response_dict["formulations"]) and ("informations" in response_dict["formulations"]):
          # Ensure CR content is handled, then clean bold/header
          cr_content = response_dict["CR"]
          processed_cr = clean_bold(clean_header(cr_content)).strip()
          return (processed_cr, response_dict["formulations"]["diagnostics"], response_dict["formulations"]["informations"])
        else:
          return (None, None, None)
      else:
        return (None, None, None)
    else:
      return (None, None, None)
  else:
    return (None, None, None)