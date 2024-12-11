import argparse
from base_types import *
import json
import grader
import serialization
import querier
import sys
import os
import validation
import datetime

def load_problems(base_path):
	return serialization.get_problems(base_path)

def validate_problems(base_path):
	validation_results = {}
	
	problemsJSON = serialization.get_problems_json(base_path)
	
	for fileName, json in problemsJSON.items():
		validation_results[fileName] = validation.validate_problem_json(json)
		print(f'{fileName}: {validation_results[fileName]}')
	return validation_results

def generate_solutions(base_path, problem_definitions, models):
	solutions = []	
	for model in models:
		for problem_definition in problem_definitions:
			inputs = problem_definition.get_llm_problem_inputs()
			for problem_input in inputs:
				solution = model.generate_solution(problem_input)
				solutions.append(solution)
				serialization.save_solution(base_path, solution)
	return solutions
	
def load_solutions(base_path, models):
	solutions = []
	for model in models:
		solutions += serialization.load_solutions(base_path, model.model_identifier)
	return solutions

def grade_solutions(base_path, problem_definitions, models, graders, current_report_paths):
	gradingOutputs = []
	for grader in graders:
		if not grader.can_grade(problem_definitions):
			continue
		for model in models:
			print(f'Grading solutions for {base_path} from model {model.model_identifier} with grader {grader.identifier}')
			solutions = serialization.get_solutions(base_path, model.model_identifier)
			grades = grader.grade(problem_definitions, solutions)
			current_report_path = current_report_paths[model]
			serialization.save_grades(base_path, grades, current_report_path)
			gradingOutputs.append(grades)
	print(gradingOutputs)
	return gradingOutputs
	
def load_grades(base_path, models, graders):
	gradingOutputs = []
	for grader in graders:
		for model in models:
			gradingOutputs.append(serialization.get_grades(base_path, model.model_identifier, grader.identifier))

	return gradingOutputs
	
def print_header(text, symbol='#'):
	# Convert text to uppercase
	text = text.upper()
	
	# Get the length of the text, plus 4 to account for spaces and surrounding symbols
	length = len(text) + 4
	
	# Create the decorative line
	decoration = symbol * length
	
	# Combine everything together
	result = f"{decoration}\n{symbol} {text} {symbol}\n{decoration}"
	
	print(f'\n{result}\n')

def main():
	parser = argparse.ArgumentParser(description="Run specified phases of the grading process.")
	parser.add_argument('--base_path', nargs='*', default=None, help="The base path(s) for data files. If this arg is not set, run all problem sets in ./problem_sets")
	parser.add_argument('--validate', action='store_true', help="Validate the problem definition JSON.")
	parser.add_argument('--generate', action='store_true', help="Generate solutions for problems.")
	parser.add_argument('--grade', action='store_true', help="Grade the generated solutions.")
	parser.add_argument('--model', required='--generate' in sys.argv or '--grade' in sys.argv, nargs='+', help=f"The model(s) to use for generating solutions The following model names can be queried through the OpenAI API: {querier.OpenAIModelQuerier.supported_model_names()}")
	parser.add_argument('--grader', required='--grade' in sys.argv, nargs='+', help=f"The grader(s) to use for grading solutions. Valid graders: {grader.Grader.all_graders()}")
	parser.add_argument('--force-human', action='store_true', help="Always use the interactive human model querier.")
	parser.add_argument('--report-path', default=None, help="Location in which to store reports generated during each run. Default= ./reports")
	args = parser.parse_args()

	problem_definitions = []
	
	if args.model:
		models = querier.AIModelQuerier.resolve_queriers(args.model, args.force_human)
	if args.grader:
		graders = grader.Grader.resolve_graders(args.grader)
	
	if args.base_path is None:
		args.base_path = [os.path.join('problem_sets', d) for d in os.listdir('problem_sets') if os.path.isdir(os.path.join('problem_sets', d))]

	if args.report_path is None:
		args.report_path = 'reports'
		
	if args.validate:
		print_header('Validation')
		print("Validating problems…")
		all_validation_results = {x: validate_problems(x) for x in args.base_path}
		print("Validation results:")
		for base_path, validation_results in all_validation_results.items():
			print(f"{base_path}:")
			for fileName, validation_result in validation_results.items():
				print(f"\t{fileName}: {validation_result}")
	
	if args.generate or args.grade:
		# generate timestamp to identify final report:
		timestamp = datetime.datetime.now().strftime("%m-%d-%Y--%H-%M-%S")
		current_report_paths = {m: os.path.join(args.report_path, "report-" + m.model_identifier + "-" + timestamp + ".json") for m in models}

		print_header('Problems')
		print("Loading problems…")
		problem_sets = {x: load_problems(x) for x in args.base_path}
	
		# Run benchmarks on all problem sets sequentially
		for base_path, problem_definitions in problem_sets.items():
			print(f"\n***\n*** Problem set {base_path}\n***\n")
			for problem_definition in problem_definitions:
				print(problem_definition)
				print()
				
			if args.generate:
				print_header('Generation')
				print("Generating solutions…")
				solutions = generate_solutions(base_path, problem_definitions, models)
				print(solutions)
			
			if args.grade:
				print_header('Grading')
				print("Grading solutions…")
				grading_outputs = grade_solutions(base_path, problem_definitions, models, graders, current_report_paths)
	
				for output in grading_outputs:
					print(output.str_including_solutions())
	
				print()
	
				for output in grading_outputs:
					print(output)

if __name__ == "__main__":
	main()
