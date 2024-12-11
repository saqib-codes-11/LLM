# Migration guide

Migrating from your current benchmarking suite to the format used in this framework has three main steps:

1. Examine and refine the problem set and evaluation metrics.
2. Migrate each of the problems to the standard problem JSON format.
3. Migrate the evaluation mechanism to the `Grader` class.

We will go through each of these in turn below. You can also see [an example ChatGPT session](https://chat.openai.com/share/3ee72075-7797-4ccb-905d-f6ad71c8fafa) that goes through these steps.

## Examine and refine the problem set and evaluation metrics

Some things to consider:

- Are the problems described consistently and with enough detail that an LLM can reasonably be expected to provide a correct solution?
- Can the solutions be graded in a quantitative manner?
	- This may require developing specific test cases, an ideal solution, or other additional information about the problem. (Generative AI is great for this!)

#### Sample LLM prompt
	
> I plan to provide the coding problems below to an LLM like yourself. For each one, expand on the problem definition so that it provides the following specific information that will enable the LLM to produce a consistent solution: prompt, function signature, example input and output, and a correctness test suite.

#### Example

Suppose that the problem set currently has problems of this form:

- Problem Description: Write a function named that takes two numbers and returns their sum.

Adding more detail on the expected format of the solution, along with some test cases, will make the resulting solution easier to grade and make it easier to convert to the structured format used in this testing framework:

**Prompt**:
Write a function named 'add' that takes two integer arguments, 'a' and 'b', and returns their sum.

**Function Signature:**
```python
def add(a: int, b: int) -> int:
```

**Example:**
```python
# Function Call
add(5, 3)

# Output
8
```

**Correctness Test Cases:**
1. Test Case 1:
   - Function Call: `add(4, 7)`
   - Expected Output: `11`
2. Test Case 2:
   - Function Call: `add(-5, -2)`
   - Expected Output: `-7`
3. Test Case 3:
   - Function Call: `add(0, 0)`
   - Expected Output: `0`
4. Test Case 4:
   - Function Call: `add(10, 5)`
   - Expected Output: `15`
5. Test Case 5:
   - Function Call: `add(-3, 3)`
   - Expected Output: `0`

## Migrate to the standard problem JSON

Before proceeding, look through the [problem definition JSON specification](problem_definition.md) to understand its overall format.

### Step 1: Identify appropriate few-shot examples of problems in the existing format

Identify a few problems that are broadly representative of your problem set and can be provided to an LLM as a starting point for the conversion process. Ideally, these problems would be of varying complexity.

#### Examples

**Prompt**:
Write a function named 'add' that takes two integer arguments, 'a' and 'b', and returns their sum.

**Function Signature:**
```python
def add(a: int, b: int) -> int:
```

**Example:**
```python
# Function Call
add(5, 3)

# Output
8
```

**Correctness Test Cases:**
1. Test Case 1:
   - Function Call: `add(4, 7)`
   - Expected Output: `11`
2. Test Case 2:
   - Function Call: `add(-5, -2)`
   - Expected Output: `-7`
3. Test Case 3:
   - Function Call: `add(0, 0)`
   - Expected Output: `0`
4. Test Case 4:
   - Function Call: `add(10, 5)`
   - Expected Output: `15`
5. Test Case 5:
   - Function Call: `add(-3, 3)`
   - Expected Output: `0`

**Prompt**:
Write a function named 'find_max' that takes two integer arguments, 'a' and 'b', and returns the larger value between them.

**Function Signature:**
```python
def find_max(a: int, b: int) -> int:
```

**Example:**
```python
# Function Call
find_max(4, 7)

# Output
7
```

**Correctness Test Cases:**
1. Test Case 1:
   - Function Call: `find_max(4, 7)`
   - Expected Output: `7`
2. Test Case 2:
   - Function Call: `find_max(-5, -2)`
   - Expected Output: `-2`
3. Test Case 3:
   - Function Call: `find_max(0, 0)`
   - Expected Output: `0`
4. Test Case 4:
   - Function Call: `find_max(10, 5)`
   - Expected Output: `10`


### Step 2: Identify relevant fields for your problem set and a conversion approach

Determine which fields are relevant for your problem type and how the output could be structured. This is a task that can be delegated to an LLM with a prompt like the one below.

> I want to convert problems in textual form into JSON that conforms to a specified format. Given example problems below, develop a general approach for converting the data in the problems into valid JSON. Your approach should be applicable to other problems in this general format.
> 
> Problems:
> <problem definition from Step 1>
> <problem definition from Step 1>
> 
> Problem Definition JSON Specification:
> {
> 	"identifier": "<string>",
> 	"prompts": [
> 		{
> 			"prompt_id": "<string>",
> 			"prompt": "<string>",
> 			"genericize": <boolean> (Optional),
> 			"sample_inputs_outputs": [
> 				{
> 					"input": {"<parameter_name>": "<parameter_value>", ...},
> 					"expected_output": ["<output_value>", ...]
> 				},
> 				...
> 			],
> 			"input_code": "<string> (Optional)"
> 		},
> 		...
> 	],
> 	"function_prototype": {
> 		"function_name": "<string>",
> 		"parameters": [
> 			{
> 				"name": "<string>",
> 				"type": "<string>"
> 			},
> 			...
> 		],
> 		"return_values": [
> 			{
> 				"type": "<string>"
> 			},
> 			...
> 		]
> 	},
> 	"correctness_test_suite": [
> 		{
> 			"input": {"<parameter_name>": "<parameter_value>", ...},
> 			"expected_output": ["<output_value>", ...]
> 		},
> 		...
> 	],
> 	"optimal_solution": "<string> (Optional)",
> 	"tags": ["<string>", ...] (Optional)
> }


### Step 3: Create a prompt for conversion

Next, come up with a prompt that can be provided to an LLM to convert from your format to the structured JSON format. You can use an LLM to come up with this prompt, using an approach like the below:

> Now, create a prompt that I could provide to an LLM like you. The prompt should contain the problem definition in the original format and asks for valid JSON for the fields you identified in the output problem definition JSON format.
> 
> The prompt should be completely self-contained, not relying on any information previously provided in this conversation.

### Step 3: Convert to the JSON Based on Relevant Fields

For each problem (or possibly a small set of problems), use the prompt generated above to perform the conversion.

#### Example prompt

> **Problem Definition:**
> 
> **Prompt**:
> Write a function named `calculate_average` that takes three numbers as arguments and returns their average.
> 
> **Function Signature:**
> def calculate_average(a: float, b: float, c: float) -> float:
> 
> **Example Input and Output:**
> Input: 1.0, 2.0, 3.0
> Output: 2.0
> 
> Input: -1.0, 0.0, 1.0
> Output: 0.0
> 
> #### Correctness Test Suite:
> assert calculate_average(0.0, 0.0, 0.0) == 0.0
> assert calculate_average(-1.0, 1.0, 1.0) == 0.3333333333333333
> assert calculate_average(100.0, 200.0, 300.0) == 200.0
> assert calculate_average(1.25, 2.5, 3.75) == 2.5
> 
> **Task:**
> Your task is to convert the above problem definition into a valid JSON format based on the following specifications:
> 
> {
> 	"identifier": "<string>",
> 	"prompts": [
> 		{
> 			"prompt_id": "<string>",
> 			"prompt": "<string>",
> 			"sample_inputs_outputs": [
> 				{
> 					"input": {"<parameter_name>": "<parameter_value>", ...},
> 					"expected_output": ["<output_value>", ...]
> 				},
> 				...
> 			],
> 			"input_code": "<string> (Optional)"
> 		},
> 		...
> 	],
> 	"function_prototype": {
> 		"function_name": "<string>",
> 		"parameters": [
> 			{
> 				"name": "<string>",
> 				"type": "<string>"
> 			},
> 			...
> 		],
> 		"return_values": [
> 			{
> 				"type": "<string>"
> 			},
> 			...
> 		]
> 	},
> 	"correctness_test_suite": [
> 		{
> 			"input": {"<parameter_name>": "<parameter_value>", ...},
> 			"expected_output": ["<output_value>", ...]
> 		},
> 		...
> 	],
> 	"optimal_solution": "<string> (Optional)",
> 	"tags": ["<string>", ...] (Optional)
> }
>
> Please ensure that:
> - The `identifier` field contains a unique identifier for the problem.
> - The `prompts` field contains a list with at least one object, representing the problem prompt. Each object in the list should have a unique `prompt_id`.
> - The `sample_inputs_outputs` field within the `prompts` object contains a list of objects, each representing a pair of example input and expected output.
> - The `function_prototype` field contains an object representing the function prototype, including the function name, parameters, and return values.
> - The `correctness_test_suite` field contains a list of objects, each representing a pair of input and expected output for testing the correctness of a solution.
> 
> Provide the resulting JSON.


#### Example output

> Here's the JSON format for the provided problem definition:
> 
> {
> 	"identifier": "calculate_average_001",
> 	"prompts": [
> 		{
> 			"prompt_id": "calculate_average_prompt_01",
> 			"prompt": "Write a function named `calculate_average` that takes three numbers as arguments and returns their average.",
> 			"sample_inputs_outputs": [
> 				{
> 					"input": {"a": 1.0, "b": 2.0, "c": 3.0},
> 					"expected_output": [2.0]
> 				},
> 				{
> 					"input": {"a": -1.0, "b": 0.0, "c": 1.0},
> 					"expected_output": [0.0]
> 				}
> 			]
> 		}
> 	],
> 	"function_prototype": {
> 		"function_name": "calculate_average",
> 		"parameters": [
> 			{
> 				"name": "a",
> 				"type": "float"
> 			},
> 			{
> 				"name": "b",
> 				"type": "float"
> 			},
> 			{
> 				"name": "c",
> 				"type": "float"
> 			}
> 		],
> 		"return_values": [
> 			{
> 				"type": "float"
> 			}
> 		]
> 	},
> 	"correctness_test_suite": [
> 		{
> 			"input": {"a": 0.0, "b": 0.0, "c": 0.0},
> 			"expected_output": [0.0]
> 		},
> 		{
> 			"input": {"a": -1.0, "b": 1.0, "c": 1.0},
> 			"expected_output": [0.3333333333333333]
> 		},
> 		{
> 			"input": {"a": 100.0, "b": 200.0, "c": 300.0},
> 			"expected_output": [200.0]
> 		},
> 		{
> 			"input": {"a": 1.25, "b": 2.5, "c": 3.75},
> 			"expected_output": [2.5]
> 		}
> 	]
> }
> 
> Note: I've made up a unique identifier for the problem as "calculate_average_001" and a unique prompt ID as "calculate_average_prompt_01". The `optimal_solution` and `tags` fields are optional and are not included in this JSON. If you have those details, you can add them to the JSON structure.

### Step 4: Save each problem JSON to a separate file

The file name should have the format {problem_id}.json. Save your problem set in a subdirectory of the `problem_sets` directory inside the project.

### Step 5: Validate your problem definitions in the framework

The following command will examine the JSON for each problem and ensure that it conforms to the specification. Address any errors it finds before continuing.

`python3 benchmark.py --base_path problem_sets/<problem set>/ --validate`

### Step 6: Generate solutions using the framework

Generate solutions for your problem set to generate solutions with gpt-4 as follows:

`python3 benchmark.py --base_path problem_sets/<problem set>/ --generate --model gpt-4`

It's a good idea to examine a few solutions manually by inspecting the `problem_sets/<problem set>/solutions/gpt-4/` directory to make sure they appear reasonable.

If you have provided a correctness test suite for each problem, you can then run the correctness grader with the following command:

`python3 benchmark.py --base_path problem_sets/<problem set>/ --grade --model gpt-4 --grader correctness`

Examine the output to determine if the failures make sense.

## Implement a grader for your problems

Depending on the format of your problems, you may or may not need to implement a grader. If you are simply testing correctness, the built-in `CorrectnessGrader` can test the solutions generated from your prompts and provide a score. If your benchmark grades solutions based on other metrics, read on!

### Grader interface

Take a look at [`grader.py`](grader.py), which contains the definition of the Grader abstract base class as well as a couple of example concrete subclasses. You will need to implement a new subclass that implements the following methods:

```
@classmethod
@property
@abstractmethod
def identifier(self) -> str:
	"""
	A human-readable identifier for the grader.
	"""
	pass
	
@abstractmethod
def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
	"""
	Grades the provided solutions against the problem definitions.
	"""
	pass
```

Depending on the fields in the problem definition needed for your grader, you may also need to implement the method below:

```
@classmethod
def can_grade(cls, problems: List[ProblemDefinition]) -> bool:
	"""
	Check if the current grader is capable of running the problem set.
	"""
	return True
```

The `ProblemDefinition` class is a Python version of the problem JSON, and the `LLMSolution` class contains the code provided by the LLM along with some metadata.

### Running the solutions

Many graders will want to execute the code provided by the LLM as part of the evaluation process. The `run_function` method on the abstract `Grader` class takes in the code, the function prototype, and the parameters and provides the value returned by the function.

See `CorrectnessGrader` for an example of how to use `run_function`.

### Expected output

The `grade` method of your `Grader` subclass will need to return a `GradingOutput` object, which contains a list of `SolutionGrade` objects, one per problem. The `SolutionGrade` is populated with the following properties:

- `problem_identifier` from the `ProblemDefinition`
- `prompt_identifier` from the `ProblemDefinition`
- A `score` between 0.0 and 1.0
- The `model_identifier` from the `LLMSolution`
- (Optional) A dictionary of key-value pairs providing sub-scores that make up the overall score
- (Optional) A list of strings describing issues identified during grading.

Again, take a look at the `CorrectnessGrader` for an example of how to generate the `GradingOutput`.

### Testing your grader

After generating solutions, you can test your grader with the following command:

`python3 benchmark.py --base_path problem_sets/<problem set>/ --grade --model gpt-4 --grader <grader_id>`

…where `grader_id` is the identifier your `Grader` subclass returns from its `identifier` method.

## Putting it all together

Now that you have provided your problems in the standard format and implemented your grader, you can run everything at once with the following command:

`python3 benchmark.py --base_path problem_sets/<problem set>/ --validate --generate --grade --model gpt-4 --grader <grader_id>`
