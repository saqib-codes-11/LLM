from base_types import *
import execution

def validate_parameter(parameter: dict) -> tuple:
	"""
	Validates a Parameter JSON object.

	Args:
	parameter (dict): A dictionary representing a Parameter JSON object.

	Returns:
	tuple: A tuple containing a boolean and a string. The boolean is True if the parameter conforms to the 
		   specified format, False otherwise. The string contains the error message if validation fails.
	"""
	# Check that all required fields are present
	required_fields = ["name", "type"]
	if not all(field in parameter for field in required_fields):
		missing_fields = [field for field in required_fields if field not in parameter]
		return False, f"Missing required fields: {', '.join(missing_fields)}"
	
	# Check that the fields are of the correct type
	if not isinstance(parameter["name"], str) or not isinstance(parameter["type"], str):
		return False, "Both 'name' and 'type' fields must be of type string."

	return True, ""

def validate_return_value(return_value: dict) -> tuple:
	"""
	Validates a ReturnValue JSON object.

	Args:
	return_value (dict): A dictionary representing a ReturnValue JSON object.

	Returns:
	tuple: A tuple containing a boolean and a string. The boolean is True if the return_value conforms to the 
		   specified format, False otherwise. The string contains the error message if validation fails.
	"""
	# Check that all required fields are present
	required_fields = ["type"]
	if not all(field in return_value for field in required_fields):
		missing_fields = [field for field in required_fields if field not in return_value]
		return False, f"Missing required fields: {', '.join(missing_fields)}"
	
	# Check that the fields are of the correct type
	if not isinstance(return_value["type"], str):
		return False, "'type' field must be of type string."

	return True, ""

def validate_function_prototype(function_prototype: dict) -> tuple:
	"""
	Validates a FunctionPrototype JSON object.
	
	Args:
	function_prototype (dict): A dictionary representing a FunctionPrototype JSON object.
	
	Returns:
	tuple: A tuple containing a boolean and a string. The boolean is True if the function_prototype conforms to the 
		   specified format, False otherwise. The string contains the error message if validation fails.
	"""
	# Check that all required fields are present
	required_fields = ["function_name", "parameters", "return_values"]
	if not all(field in function_prototype for field in required_fields):
		missing_fields = [field for field in required_fields if field not in function_prototype]
		return False, f"Missing required fields: {', '.join(missing_fields)}"
	
	# Check that the fields are of the correct type
	if not isinstance(function_prototype["function_name"], str):
		return False, f"'function_name' field must be of type string. Found: {type(function_prototype['function_name']).__name__}."
	
	# Check that parameters and return_values are arrays
	if not isinstance(function_prototype["parameters"], list):
		return False, f"'parameters' field must be of type array. Found: {type(function_prototype['parameters']).__name__}."
	if not isinstance(function_prototype["return_values"], list):
		return False, f"'return_values' field must be of type array. Found: {type(function_prototype['return_values']).__name__}."
	
	# Validate each Parameter and ReturnValue JSON object
	for param in function_prototype["parameters"]:
		valid, error = validate_parameter(param)
		if not valid:
			return False, f"Invalid Parameter JSON object: {error}"
	
	for ret_val in function_prototype["return_values"]:
		valid, error = validate_return_value(ret_val)
		if not valid:
			return False, f"Invalid ReturnValue JSON object: {error}"
	
	return True, ""

def validate_test_case(test_case: dict, function_prototype: FunctionPrototype) -> tuple:
	"""
	Validates a TestCase JSON object.

	Args:
	test_case (dict): A dictionary representing a TestCase JSON object.

	Returns:
	tuple: A tuple containing a boolean and a string. The boolean is True if the test_case conforms to the 
		   specified format, False otherwise. The string contains the error message if validation fails.
	"""
	# Check that all required fields are present
	required_fields = ["input", "expected_output"]
	if not all(field in test_case for field in required_fields):
		missing_fields = [field for field in required_fields if field not in test_case]
		return False, f"Missing required fields: {', '.join(missing_fields)}"
	
	# Check that input is an object and expected_output is an array
	if not isinstance(test_case["input"], dict):
		return False, f"'input' field must be of type object. Found: {type(test_case['input']).__name__}."
	if not isinstance(test_case["expected_output"], list):
		return False, f"'expected_output' field must be of type array. Found: {type(test_case['expected_output']).__name__}."

	try:
		test_case_obj = TestCase(test_case)
		parameters = function_prototype.get_ordered_parameter_values(test_case_obj)
		expected_result = function_prototype.get_return_values(test_case_obj)
	except Exception as e:
		return False, f"Got exception while parsing test case: {e}"
	return True, ""

def validate_prompt(prompt: dict, function_prototype=None) -> tuple:
	"""
	Validates a Prompt JSON object.

	Args:
	prompt (dict): A dictionary representing a Prompt JSON object.

	Returns:
	tuple: A tuple containing a boolean and a string. The boolean is True if the prompt conforms to the 
		   specified format, False otherwise. The string contains the error message if validation fails.
	"""
	# Check that all required fields are present
	required_fields = ["prompt_id", "prompt"]
	if not all(field in prompt for field in required_fields):
		missing_fields = [field for field in required_fields if field not in prompt]
		return False, f"Missing required fields: {', '.join(missing_fields)}"
	
	# Check that the fields are of the correct type
	if not isinstance(prompt["prompt_id"], str):
		return False, f"'prompt_id' field must be of type string. Found: {type(prompt['prompt_id']).__name__}."
	if not isinstance(prompt["prompt"], str):
		return False, f"'prompt' field must be of type string. Found: {type(prompt['prompt']).__name__}."
	
	# Check that optional fields, if present, are of the correct type
	if "genericize" in prompt and not isinstance(prompt["genericize"], bool):
		return False, f"'genericize' field must be of type boolean. Found: {type(prompt['genericize']).__name__}."
	
	if "sample_inputs_outputs" in prompt:
		if function_prototype is None:
			return False, f"Function prototype must be present if a correctness test suite is provided."
		if not isinstance(prompt["sample_inputs_outputs"], list):
			return False, "'sample_inputs_outputs' field must be of type array."
		# Validate each TestCase JSON object
		for test_case in prompt["sample_inputs_outputs"]:
			valid, error = validate_test_case(test_case, function_prototype)
			if not valid:
				return False, f"Invalid TestCase JSON object in 'sample_inputs_outputs': {error}"

	if "input_code" in prompt and not isinstance(prompt["input_code"], str):
		return False, f"'input_code' field must be of type string. Found: {type(prompt['input_code']).__name__}."

	return True, ""

def validate_problem_json(problem_json: dict) -> (bool, str):
	"""
	Validates the top-level problem JSON structure.
	
	Args:
	problem_json (dict): A dictionary representing the top-level problem JSON object.
	
	Returns:
	tuple: A tuple containing a boolean and a string. 
	   	The boolean is True if the problem_json conforms to the specified format, False otherwise.
	   	The string provides an error message in case of a failure.
	"""
	# Check that all required fields are present
	required_fields = ["identifier", "prompts"]
	if not all(field in problem_json for field in required_fields):
		missing_fields = [field for field in required_fields if field not in problem_json]
		return False, f"Missing required fields: {', '.join(missing_fields)}"
	
	# Check that the fields are of the correct type
	if not isinstance(problem_json["identifier"], str):
		return False, "Field 'identifier' should be a string"
	
	# Check that prompts, correctness_test_suite, and tags are arrays
	if not isinstance(problem_json["prompts"], list):
		return False, "Field 'prompts' should be an array"
	
	if "correctness_test_suite" in problem_json and not isinstance(problem_json["correctness_test_suite"], list):
		return False, "Field 'correctness_test_suite' should be an array"
	
	if "tags" in problem_json and not isinstance(problem_json["tags"], list):
		return False, "Field 'tags' should be an array"
	
	# Validate each Prompt, TestCase, and FunctionPrototype JSON object
	for index, prompt in enumerate(problem_json["prompts"]):
		function_prototype = FunctionPrototype(problem_json["function_prototype"]) if "function_prototype" in problem_json else None
		valid, error_message = validate_prompt(prompt, function_prototype)
		if not valid:
			return False, f"Invalid prompt at index {index}: {error_message}"
	
	if "correctness_test_suite" in problem_json:
		if not "function_prototype" in problem_json:
			return False, f"Function prototype must be present if a correctness test suite is provided."
		function_prototype = FunctionPrototype(problem_json["function_prototype"])	

		for index, test_case in enumerate(problem_json["correctness_test_suite"]):
			valid, error_message = validate_test_case(test_case, function_prototype)
			if not valid:
				return False, f"Invalid test case in 'correctness_test_suite' at index {index}: {error_message}"
	
	if "function_prototype" in problem_json:
		valid, error_message = validate_function_prototype(problem_json["function_prototype"])
		if not valid:
			return False, f"Invalid function prototype: {error_message}"
	
	# Check that optional fields, if present, are of the correct type
	if "optimal_solution" in problem_json and not isinstance(problem_json["optimal_solution"], str):
		return False, "Field 'optimal_solution' should be a string"
	
	if "tags" in problem_json and not all(isinstance(tag, str) for tag in problem_json["tags"]):
		return False, "All elements in field 'tags' should be strings"
		
	if 'optimal_solution' in problem_json and 'correctness_test_suite' in problem_json:
		# Ensure that the optimal solution passes the correctness test suite
		for index, test_case in enumerate(problem_json["correctness_test_suite"]):
			test_case_obj = TestCase(test_case)
			parameters = function_prototype.get_ordered_parameter_values(test_case_obj)
			expected_result = function_prototype.get_return_values(test_case_obj)
			execution_results = execution.execute_function(problem_json["optimal_solution"], parameters, iterations=1, collect_cpu_time=False, collect_memory_usage=False)
			parameters_desc = ', '.join([f'{p} {type(p)}' for p in parameters])
			if execution_results.error:
				return False, f"Optimal solution encountered error for test case {test_case_obj}. Parameters: {parameters_desc}; Error: {execution_results.error}"
			if expected_result != execution_results.result:
				return False, f"Optimal solution did not pass test case {test_case_obj}. Parameters: {parameters_desc}; Expected result: {expected_result} {type(expected_result)}; Actual result: {execution_results.result} {type(execution_results.result)}"
	
	return True, "Validation successful"
