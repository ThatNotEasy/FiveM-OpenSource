"""
Core converter functionality for ESX to QB-Core and QB-Core to ESX conversions.
"""
import os
import re
import shutil
from typing import List, Tuple, Dict, Optional, Callable


def manual_replace(script: str, direction: str = "ESX to QB-Core") -> str:
    """
    Perform manual replacements for specific code patterns.

    Args:
        script (str): The content of the script file.
        direction (str): Conversion direction.

    Returns:
        str: The modified script content.
    """
    if direction == "ESX to QB-Core":
        replacements = {
            "ESX = exports['es_extended']:getSharedObject()": "local QBCore = exports['qb-core']:GetCoreObject()",
        }
    else:  # QB-Core to ESX
        replacements = {
            "local QBCore = exports['qb-core']:GetCoreObject()": "ESX = exports['es_extended']:getSharedObject()",
            "QBCore = exports['qb-core']:GetCoreObject()": "ESX = exports['es_extended']:getSharedObject()",
        }

    for old, new in replacements.items():
        script = script.replace(old, new)

    return script


def convert_script(
    script: str, 
    patterns: List[Tuple[str, str]], 
    include_sql: bool = False, 
    sql_patterns: Optional[List[Tuple[str, str]]] = None,
    direction: str = "ESX to QB-Core"
) -> str:
    """
    Convert the script content based on the provided patterns.

    Args:
        script (str): The original script content.
        patterns (List[Tuple[str, str]]): List of tuples containing old and new patterns.
        include_sql (bool, optional): Flag to include SQL patterns. Defaults to False.
        sql_patterns (Optional[List[Tuple[str, str]]], optional): List of SQL pattern tuples. Defaults to None.
        direction (str, optional): Conversion direction. Defaults to "ESX to QB-Core".

    Returns:
        str: The converted script content.
    """
    if sql_patterns is None:
        sql_patterns = []
        
    script = manual_replace(script, direction)
    for old, new in patterns:
        script = script.replace(old, new)
    
    if include_sql:
        for old, new in sql_patterns:
            script = script.replace(old, new)
            
    return script


def process_file(
    input_path: str,
    output_path: str,
    patterns: List[Tuple[str, str]], 
    direction: str, 
    include_sql: bool, 
    sql_patterns: List[Tuple[str, str]]
) -> bool:
    """
    Process a single Lua script file, converting its content based on the patterns.

    Args:
        input_path (str): Path to the input Lua script file.
        output_path (str): Path to the output Lua script file.
        patterns (List[Tuple[str, str]]): List of tuples containing old and new patterns.
        direction (str): Conversion direction ("ESX to QB-Core" or "QB-Core to ESX").
        include_sql (bool): Flag to include SQL patterns.
        sql_patterns (List[Tuple[str, str]]): List of SQL pattern tuples.

    Returns:
        bool: True if changes were made, False otherwise
    """
    try:
        with open(input_path, "r", encoding="utf-8") as file:
            content = file.read()

        converted = convert_script(content, patterns, include_sql, sql_patterns, direction)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if content != converted:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(converted)
            return True
        else:
            # Copy file even if no changes
            shutil.copy2(input_path, output_path)
            return False
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        return False


def process_folder(
    folder_path: str, 
    patterns: List[Tuple[str, str]], 
    direction: str, 
    include_sql: bool, 
    sql_patterns: List[Tuple[str, str]],
    callback: Optional[Callable[[str], None]] = None,
    output_prefix: str = "qb-"
) -> Dict[str, int]:
    """
    Recursively process all Lua script files in the specified folder.

    Args:
        folder_path (str): Path to the folder containing Lua script files.
        patterns (List[Tuple[str, str]]): List of tuples containing old and new patterns.
        direction (str): Conversion direction ("ESX to QB-Core" or "QB-Core to ESX").
        include_sql (bool): Flag to include SQL patterns.
        sql_patterns (List[Tuple[str, str]]): List of SQL pattern tuples.
        callback (Optional[Callable[[str], None]], optional): Callback function for progress updates. Defaults to None.
        output_prefix (str, optional): Prefix for the output folder. Defaults to "qb-".

    Returns:
        Dict[str, int]: Statistics about the conversion process
    """
    stats = {
        "total_files": 0,
        "converted_files": 0,
        "skipped_files": 0,
        "error_files": 0
    }
    
    # Create output folder path with prefix
    parent_dir = os.path.dirname(folder_path)
    folder_name = os.path.basename(folder_path)
    output_folder = os.path.join(parent_dir, f"{output_prefix}{folder_name}")
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    for root, dirs, files in os.walk(folder_path):
        # Calculate relative path from input folder
        rel_path = os.path.relpath(root, folder_path)
        
        # Create corresponding output directory
        if rel_path != ".":
            output_dir = os.path.join(output_folder, rel_path)
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = output_folder
        
        for file in files:
            if file.endswith(".lua"):
                input_path = os.path.join(root, file)
                output_path = os.path.join(output_dir, file)
                stats["total_files"] += 1
                
                try:
                    was_converted = process_file(input_path, output_path, patterns, direction, include_sql, sql_patterns)
                    if was_converted:
                        stats["converted_files"] += 1
                        if callback:
                            callback(f"Converted: {output_path}")
                    else:
                        stats["skipped_files"] += 1
                        if callback:
                            callback(f"No changes needed: {output_path}")
                except Exception as e:
                    stats["error_files"] += 1
                    if callback:
                        callback(f"Error processing {input_path}: {str(e)}")
    
    # Copy non-lua files as well
    copy_non_lua_files(folder_path, output_folder, callback)
    
    return stats


def copy_non_lua_files(src_folder: str, dst_folder: str, callback: Optional[Callable[[str], None]] = None):
    """
    Copy all non-Lua files from source to destination folder.

    Args:
        src_folder (str): Source folder path.
        dst_folder (str): Destination folder path.
        callback (Optional[Callable[[str], None]], optional): Callback function for progress updates.
    """
    for root, dirs, files in os.walk(src_folder):
        rel_path = os.path.relpath(root, src_folder)
        
        if rel_path != ".":
            output_dir = os.path.join(dst_folder, rel_path)
        else:
            output_dir = dst_folder
        
        for file in files:
            if not file.endswith(".lua"):
                input_path = os.path.join(root, file)
                output_path = os.path.join(output_dir, file)
                
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    shutil.copy2(input_path, output_path)
                    if callback:
                        callback(f"Copied: {output_path}")
                except Exception as e:
                    if callback:
                        callback(f"Error copying {input_path}: {str(e)}")
