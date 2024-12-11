
# Problem Definition JSON specification

## Top-Level Problem JSON Structure

```json
{
	"identifier": "<string>",
	"prompts": [
		<Prompt JSON Object>,
		...
	],
	"function_prototype": <FunctionPrototype JSON Object>,
	"correctness_test_suite": [
		<TestCase JSON Object>,
		...
	] (Optional),
	"optimal_solution": "<string> (Optional)",
	"tags": [
		"<string>",
		...
	] (Optional)
}
```

### Fields Description:

1. **identifier** (String):
	- A string representing the unique identifier of the problem definition.
  
2. **prompts** (Array of `Prompt` JSON Objects):
	- An array of JSON objects representing the prompts. Each object should adhere to the JSON format expected by the `Prompt` class.

3. **function_prototype** (`FunctionPrototype` JSON Object):
	- A JSON object representing the function prototype. The object should adhere to the JSON format expected by the `FunctionPrototype` class.

4. **correctness_test_suite** (Array of `TestCase` JSON Objects, Optional):
	- An optional array of JSON objects representing the test cases for correctness. Each object should adhere to the JSON format expected by the `TestCase` class. If not provided, the default value is an empty array.

5. **optimal_solution** (String, Optional):
	- An optional string representing the optimal solution to the problem. If not provided, the default value is `null`.

6. **tags** (Array of Strings, Optional):
	- An optional array of strings representing tags associated with the problem definition. If not provided, the default value is `null`.

---

## `FunctionPrototype` JSON Structure:

```json
{
	"function_name": "<string>",
	"parameters": [
		<Parameter JSON Object>,
		...
	],
	"return_values": [
		<ReturnValue JSON Object>,
		...
	]
}
```

### Fields Description:

- **function_name** (String):
	- A string representing the name of the function.
  
- **parameters** (Array of `Parameter` JSON Objects):
	- An array of JSON objects representing the parameters of the function. Each object should adhere to the JSON format expected by the `Parameter` class.

- **return_values** (Array of `ReturnValue` JSON Objects):
	- An array of JSON objects representing the return values of the function. Each object should adhere to the JSON format expected by the `ReturnValue` class.

---

## `Parameter` JSON Structure

```json
{
	"name": "<string>",
	"type": "<string>"
}
```

### Fields Description:

- **name** (String):
	- A string representing the name of the parameter.

- **type** (String):
	- A string representing the type of the parameter.

---

## `ReturnValue` JSON Structure

```json
{
	"type": "<string>"
}
```

### Fields Description

- **type** (String):
	- A string representing the type of the return value.


## `TestCase` JSON Structure:

```json
{
	"input": {
		"<parameter_name>": "<parameter_value>",
		...
	},
	"expected_output": [
		"<output_value>",
		...
	]
}
```

### Fields Description

- **input** (Object):
	- An object where each key-value pair represents a parameter name and its corresponding value.

- expected_output (Array):
	- An array where each element represents an expected output value.


## `Prompt` JSON Structure

```json
{
	"prompt_id": "<string>",
	"prompt": "<string>",
	"genericize": <boolean> (Optional),
	"sample_inputs_outputs": [
		<TestCase JSON Object>,
		...
	] (Optional),
	"input_code": "<string> (Optional)"
}
```

### Fields Description

- **prompt_id** (String):
	- A string representing the unique identifier of the prompt.

- **prompt** (String):
	- A string representing the text of the prompt.

- **genericize** (Boolean, Optional):
	- An optional boolean value indicating whether to genericize the prompt or not.

- **sample_inputs_outputs** (Array of `TestCase` JSON Objects, Optional):
	- An optional array of JSON objects representing the sample inputs and outputs. Each object should adhere to the JSON format expected by the `TestCase` class.

- **input_code** (String, Optional):
	- An optional string representing the input code for the prompt. If not provided, the default value is `null`.
