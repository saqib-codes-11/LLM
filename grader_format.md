## JSON Specification for `Issue`

```json
{
	"issue_category": "<string>",
	"issue_description": "<string>"
}
```

- `issue_category`: (String) Category of the issue.
- `issue_description`: (String) Description of the issue.

---

## JSON Specification for `SolutionGrade`

```json
{
	"problem_identifier": "<string>",
	"prompt_identifier": "<string>",
	"model_identifier": "<string>",
	"score": <float>,
	"sub_criteria_scores": {
		"<sub_criteria_key>": <float>,
		...
	},
	"issues": [
		{
			"issue_category": "<string>",
			"issue_description": "<string>"
		},
		...
	]
}
```

- `problem_identifier`: (String) A unique identifier for the problem.
- `prompt_identifier`: (String) A unique identifier for the prompt.
- `model_identifier`: (String) A unique identifier for the model.
- `score`: (Float) The score for the solution.
- `sub_criteria_scores`: (Dictionary) Key-value pairs where the key is the sub-criteria identifier and the value is the score for that sub-criteria.
- `issues`: (Array of Objects) List of issue objects, each containing an `issue_category` (String) and `issue_description` (String).

---

## JSON Specification for `GradingOutput`

```json
{
	"solution_grades": [
		{
			"problem_identifier": "<string>",
			"prompt_identifier": "<string>",
			"model_identifier": "<string>",
			"score": <float>,
			"sub_criteria_scores": {
				"<sub_criteria_key>": <float>,
				...
			},
			"issues": [
				{
					"issue_category": "<string>",
					"issue_description": "<string>"
				},
				...
			]
		},
		...
	],
	"grader_identifier": "<string>"
}
```

- `solution_grades`: (Array of Objects) List of `SolutionGrade` objects, each containing the fields as specified in the `SolutionGrade` JSON specification.
- `grader_identifier`: (String) A unique identifier for the grader.
