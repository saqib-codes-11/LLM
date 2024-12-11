from abc import ABC, abstractmethod
from typing import Set

from base_types import *
import execution
import os
from shutil import which
import subprocess
import tempfile
import time
import tokenize


class Grader(ABC):
    """
	Abstract base class for graders.
	"""

    @classmethod
    @property
    @abstractmethod
    def identifier(self) -> str:
        """
		A human-readable identifier for the grader.
		"""
        pass

    @classmethod
    def all_graders(cls) -> List[str]:
        return [subclass.identifier for subclass in cls.__subclasses__()]
        
    @classmethod
    def resolve_graders(cls, grader_names: List[str]) -> List['Grader']:
        subclass_mapping = {subclass.identifier: subclass for subclass in cls.__subclasses__()}
        instances = []
        for grader_name in grader_names:
            subclass = subclass_mapping.get(grader_name, CorrectnessGrader)
            instances.append(subclass())
        return instances

    @classmethod
    def run_function(cls, code: str, function_prototype: FunctionPrototype, test_case: TestCase, iterations=1,
                     collect_cpu_time=False, collect_memory_usage=False) -> execution.FunctionExecutionResult:
        """
		Runs generated Python code against a given test case.
		"""
        parameters = function_prototype.get_ordered_parameter_values(test_case)
        return execution.execute_function(code, parameters, iterations, collect_cpu_time, collect_memory_usage)
        pass

    @classmethod
    def can_grade(cls, problems: List[ProblemDefinition]) -> bool:
        """
		Check if the current grader is capable of running the problem set.
		This method should be overridden by a child class if said class has stricter requirements.
		"""
        for p in problems:
            if not (all(var is not None for var in (p.identifier, p.prompts, p.function_prototype)) and len(
                    p.prompts) > 0):
                return False
        return True

    @abstractmethod
    def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
        """
		Grades the provided solutions against the problem definitions.
		"""
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"


class CorrectnessGrader(Grader):
    @classmethod
    @property
    def identifier(self):
        return "correctness"

    def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
        solutionGrades = []
        for problem in problems:
            function_prototype = problem.function_prototype
            for solution in solutions:
                number_correct = 0
                total_tests = 0
                issues = []
                if solution.problem_identifier == problem.identifier:
                    print(f"Grading problem {problem.identifier}")
                    for test_case in problem.correctness_test_suite:
                        execution_results = Grader.run_function(solution.solution_code, function_prototype, test_case)
                        expected_result = function_prototype.get_return_values(test_case)
                        actual_result = execution_results.result

                        total_tests += 1

                        if execution_results.error:
                            issues.append(
                                f"Error encountered during execution for test case {test_case}: {execution_results.error}\n{execution_results.traceback}")
                            print(issues[-1])
                        elif expected_result == actual_result:
                            number_correct += 1
                        else:
                            issues.append(
                                f"Test failed:\n\t{test_case}\n\tFunction prototype: {function_prototype}\n\tExpected result: {expected_result} {type(expected_result)}\n\tActual result: {actual_result} {type(actual_result)}")
                            print(issues[-1])

                    score = 0
                    if total_tests > 0:
                        score = number_correct / total_tests
                    grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier,
                                          score, None, issues)
                    solutionGrades.append(grade)
        return GradingOutput(solutionGrades, self.identifier)


class PerformanceGrader(Grader):
    @classmethod
    @property
    def identifier(self):
        return "performance"

    def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
        solutionGrades = []
        for problem in problems:
            function_prototype = problem.function_prototype
            for solution in solutions:
                if solution.problem_identifier == problem.identifier:
                    print(f"Grading problem {problem.identifier}")
                    total_solution_time = 0
                    total_optimal_time = 0
                    issues = []
                    for test_case in problem.correctness_test_suite:
                        iterations = 1  # Starting with 1 iteration
                        while True:  # Continue running until a break condition is met
                            solution_results = Grader.run_function(solution.solution_code, function_prototype,
                                                                   test_case, iterations=iterations,
                                                                   collect_cpu_time=True)
                            optimal_results = Grader.run_function(problem.optimal_solution, function_prototype,
                                                                  test_case, iterations=iterations,
                                                                  collect_cpu_time=True)

                            if solution_results.cpu_time is None or optimal_results.cpu_time is None:
                                break

                            total_solution_time += solution_results.cpu_time
                            total_optimal_time += optimal_results.cpu_time

                            # Check if either total time exceeds 2 seconds
                            if total_solution_time > 0.4 or total_optimal_time > 0.4:
                                break
                            else:
                                iterations *= 10  # Increase iterations by 10 times

                    if total_solution_time > 0:
                        overall_grade = min(1, total_optimal_time / total_solution_time)
                        grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier,
                                              overall_grade, None, issues)
                        solutionGrades.append(grade)
        return GradingOutput(solutionGrades, self.identifier)

    def can_grade(cls, problems: List[ProblemDefinition]) -> bool:
        """
		Check if the current grader is capable of running the problem set.
		This method should be overridden by a child class if said class has stricter requirements.
		"""
        for p in problems:
            if not (all(var is not None for var in
                        (p.identifier, p.prompts, p.function_prototype, p.optimal_solution)) and len(p.prompts) > 0):
                return False
        return True


class MemoryGrader(Grader):
    @classmethod
    @property
    def identifier(self):
        return "memory"

    def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
        solutionGrades = []
        for problem in problems:
            function_prototype = problem.function_prototype
            for solution in solutions:
                if solution.problem_identifier == problem.identifier:
                    print(f"Grading problem {problem.identifier}")
                    total_solution_peak_memory = 0
                    total_optimal_peak_memory = 0
                    issues = []
                    for test_case in problem.correctness_test_suite:
                        iterations = 10
                        solution_results = Grader.run_function(solution.solution_code, function_prototype, test_case,
                                                               iterations=iterations, collect_memory_usage=True)
                        optimal_results = Grader.run_function(problem.optimal_solution, function_prototype, test_case,
                                                              iterations=iterations, collect_memory_usage=True)
                        if solution_results.peak_memory is None or optimal_results.peak_memory is None:
                            continue

                        total_solution_peak_memory += solution_results.peak_memory
                        total_optimal_peak_memory += optimal_results.peak_memory

                    if total_solution_peak_memory > 0:
                        overall_grade = min(1, total_optimal_peak_memory / total_solution_peak_memory)

                        grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier,
                                              overall_grade, None, issues)
                        solutionGrades.append(grade)
        return GradingOutput(solutionGrades, self.identifier)


class HalsteadGrader(Grader):
    @classmethod
    @property
    def identifier(self):
        return "halstead"

    def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:

        def halstead_difficulty(code):
            operators = {'+', '-', '*', '/', '%', '//', '**', '<<', '>>', '&', '|', '^', '~', '<', '>', '<=', '>=',
                         '==', '!=',
                         'and', 'or', 'not', 'is', 'in', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=',
                         '//=', '**=',
                         '(', ')', '[', ']', '{', '}', '@', ',', ':', '.', '=', '->', '-=', '*=', '/=', '%=', '&=',
                         '|=', '^=', '<<=', '>>=', '//=', '**=', ';'}

            words = code.replace('\n', ' ').replace('\t', ' ').split(' ')
            operands = [word for word in words if not any(op in word for op in operators) and word]

            # operator_count = sum(code.count(op) for op in operators)
            operand_count = len(operands)

            unique_operators = len(set(op for op in code.split() if op in operators))
            unique_operands = len(set(operands))

            difficulty = (unique_operators / 2) * (operand_count / unique_operands)

            return difficulty

        solutionGrades =  []
        for problem in problems:
            for solution in solutions:
                if solution.problem_identifier == problem.identifier:
                    # calculate halstead for solution.solution_code
                    score = halstead_difficulty(solution.solution_code)

                    grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier,
                                          score, None, [])
                    solutionGrades.append(grade)

        return GradingOutput(solutionGrades, self.identifier)
	
class CodeCoverageGrader(Grader):
	@classmethod
	@property
	def identifier(self):
		return "codecov"
	
	def grade(self, problems:List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
		if which("pytest") is None:
			raise RuntimeError("pytest command is required to run code coverage grader")

		solution_grades = []
		for problem in problems:
			for solution in solutions:
				if solution.problem_identifier == problem.identifier:
					with tempfile.TemporaryDirectory() as temp_dir:
						# Create necessary files
						with open(os.path.join(temp_dir, "__init__.py"), "w") as f:
							f.write("")
						
						with open(os.path.join(temp_dir, "code.py"), "w") as f:
							f.write(problem.prompts[0].input_code)

						with open(os.path.join(temp_dir, "test_code.py"), "w") as f:
							f.write(f"from .code import {problem.function_prototype.function_name}\n")
							f.write(solution.solution_code)

						# Run pytest
						subprocess.run(["pytest", "--cov=.", "--cov-report", "json"], cwd=temp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
						data = json.loads(open(os.path.join(temp_dir, "coverage.json")).read())

						# Assemble score
						grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier, data["files"]["code.py"]["summary"]["percent_covered"], None, [])
						solution_grades.append(grade)

		return GradingOutput(solution_grades, self.identifier)

class HumanLikeGrader(Grader):
    """
    Grader class that calculates the human-likeness of provided solutions.
    """
    @classmethod
    @property
    def identifier(cls) -> str:
        return "humanlikeness"

    @staticmethod
    def jaccard_distance(set1: Set, set2: Set) -> float:
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return 1 - (intersection / union) if union != 0 else 0

    def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
        solutionGrades = []
        for problem in problems:
            function_prototype = problem.function_prototype
            for solution in solutions:
                issues = []
                if solution.problem_identifier == problem.identifier:
                    ai_solution_tokens = set(solution.solution_code.split())
                    optimal_solution_tokens = set(problem.optimal_solution.split())
                    distance = self.jaccard_distance(ai_solution_tokens, optimal_solution_tokens)

                    score = 1 - distance

                    grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier, score, None, issues)
                    solutionGrades.append(grade)
        return GradingOutput(solutionGrades, self.identifier)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"


import re


class CodingConventionGrader(Grader):
	@classmethod
	@property
	def identifier(self):
		return "coding_convention"

	def _check_line_length(self, code: str) -> List[str]:
		return [f"Line {i + 1} exceeds 79 characters." for i, line in enumerate(code.split('\n')) if len(line) > 79]

	def _check_multiple_blank_lines(self, code: str) -> List[str]:
		return ["Multiple blank lines found."] if re.search(r"\n\s*\n\s*\n", code) else []

	def _check_spaces_before_punctuations(self, code: str) -> List[str]:
		return [f"Space found before punctuation on line {i + 1}." for i, line in enumerate(code.split('\n')) if
				re.search(r"\s[,;:]", line)]

	def _check_naming_convention(self, code: str) -> List[str]:
		issues = []
		# Check variable and function names
		for match in re.finditer(r"def (\w+)|(\w+) =", code):
			name = match.group(1) or match.group(2)
			if not re.match(r"^[a-z_][a-z0-9_]*$", name):
				issues.append(f"Invalid function or variable name '{name}'.")

		# Check class names
		for match in re.finditer(r"class (\w+)", code):
			name = match.group(1)
			if not re.match(r"^[A-Z][a-zA-Z0-9]*$", name):
				issues.append(f"Invalid class name '{name}'.")
		return issues

	def _check_indentation(self, code: str) -> List[str]:
		return ["Inconsistent indentation found."] if re.search(r"^(    |\t)", code, re.MULTILINE) else []

	def _check_import_order_and_format(self, code: str) -> List[str]:
		issues = []
		imports = re.findall(r"^import (\w+)", code, re.MULTILINE)
		if imports != sorted(imports):
			issues.append("Imports are not in alphabetical order.")
		if re.search(r"^from .+ import \*", code, re.MULTILINE):
			issues.append("Wildcard import found.")
		return issues

	def _check_trailing_whitespace(self, code: str) -> List[str]:
		return [f"Trailing whitespace found on line {i + 1}." for i, line in enumerate(code.split('\n')) if
				line.endswith(' ')]

	def _check_space_around_operators(self, code: str) -> List[str]:
		return [f"Missing space around operator on line {i + 1}." for i, line in enumerate(code.split('\n')) if
				re.search(r"=\w|==\w|\+\w|-\w|\*\w|/\w", line)]

	def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
		solutionGrades = []
		for problem in problems:
			for solution in solutions:
				if solution.problem_identifier == problem.identifier:
					issues = []
					issues.extend(self._check_line_length(solution.solution_code))
					issues.extend(self._check_multiple_blank_lines(solution.solution_code))
					issues.extend(self._check_spaces_before_punctuations(solution.solution_code))
					issues.extend(self._check_naming_convention(solution.solution_code))
					issues.extend(self._check_indentation(solution.solution_code))
					issues.extend(self._check_import_order_and_format(solution.solution_code))
					issues.extend(self._check_trailing_whitespace(solution.solution_code))
					issues.extend(self._check_space_around_operators(solution.solution_code))

					score = 1 - len(issues) * 0.1  # Deduct 0.1 for each issue found
					score = max(score, 0)  # Ensure score doesn't go below 0

					grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier,
										  score, None, issues)
					solutionGrades.append(grade)
		return GradingOutput(solutionGrades, self.identifier)


try:
    from memory_profiler import memory_usage
except:
    pass


class SpaceEfficiencyGrader(Grader):
	@classmethod
	@property
	def identifier(self):
		return "memory_efficiency"

	def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
		solutionGrades = []
		for problem in problems:
			for solution in solutions:
				if solution.problem_identifier == problem.identifier:
					accumulated_memory_ratio = 0
					test_cases_count = len(problem.correctness_test_suite)

					for test_case in problem.correctness_test_suite:
						# Measure memory used by the solution
						solution_memory_usage = memory_usage(
							(Grader.run_function, (solution.solution_code, problem.function_prototype, test_case)),
							max_usage=True, interval=0.1, timeout=None)
						solution_memory = solution_memory_usage if solution_memory_usage else 0

						# Measure memory used by the optimal solution
						optimal_memory_usage = memory_usage(
							(Grader.run_function, (problem.optimal_solution, problem.function_prototype, test_case)),
							max_usage=True, interval=0.1, timeout=None)
						optimal_memory = optimal_memory_usage if optimal_memory_usage else 0

						# Compute the ratio of solution memory to optimal memory
						memory_ratio = solution_memory / optimal_memory if optimal_memory != 0 else 0
						accumulated_memory_ratio += memory_ratio

					# Average the memory ratios across all test cases
					averaged_memory_ratio = accumulated_memory_ratio / test_cases_count if test_cases_count != 0 else 0

					grade = SolutionGrade(
						problem.identifier,
						solution.prompt_identifier,
						solution.model_identifier,
						averaged_memory_ratio,
						None,
						[]
					)
					solutionGrades.append(grade)
		return GradingOutput(solutionGrades, self.identifier)
		
class ReuseGrader(Grader):
	@classmethod
	@property
	def identifier(self):
		return "code_reuse"
		
	def can_grade(cls, problems: List[ProblemDefinition]) -> bool:
		"""
		Check if the current grader is capable of running the problem set.
		This method should be overridden by a child class if said class has stricter requirements.
		"""
		for p in problems:
			if not (all(var is not None for var in (p.identifier, p.prompts, p.function_prototype)) and len(p.prompts) > 0 and "parent_function_prototype" in p.additional_fields):
				return False
		return True
		
	def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
		solutionGrades = []
		for problem in problems:
			print(problem.identifier)
			function_name = problem.function_prototype.function_name
			parent_function_name = problem.additional_fields["parent_function_prototype"]["function_name"]
			for solution in solutions:
				if solution.problem_identifier == problem.identifier:
					print(f"Grading problem {problem.identifier}")
					cur_grade = 0
					
					try:
						exec(solution.solution_code, globals())
						
						
						if parent_function_name in globals().get(function_name).__code__.co_names:
							cur_grade = 1
					except Exception as e:
						print("Encountered the following exception during execution: ", e)
					grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier, cur_grade)
					solutionGrades.append(grade)
		return GradingOutput(solutionGrades, self.identifier)


class VectorizeGrader(Grader):
    @classmethod
    @property
    def identifier(self) -> str:
        return "vectorization"
        
    def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
        solutionGrades = []

        for problem in problems:
            for solution in solutions:
                if solution["problem_identifier"] == problem["identifier"]:
                    # Generate random matrix/matrices
                    random_matrix = np.random.rand(10, 10).tolist()  # Converting numpy array to Python list

                    # Measure time and output for unvectorized code
                    start_time_unvectorized = time.time()
                    expected_result = self.run_unvectorized(problem["input_code"], random_matrix)
                    end_time_unvectorized = time.time()

                    # Measure time and output for vectorized code
                    start_time_vectorized = time.time()
                    actual_result = self.run_vectorized(solution["solution_code"], random_matrix)
                    end_time_vectorized = time.time()

                    # Compare results and time
                    is_correct = np.array_equal(expected_result, actual_result)
                    time_improvement = end_time_unvectorized - end_time_vectorized

                    # Append grading results
                    solutionGrades.append({
                        "problem_id": problem["identifier"],
                        "is_correct": is_correct,
                        "time_improvement": time_improvement
                    })

        return {"solutionGrades": solutionGrades}

    def run_unvectorized(self, code: str, input_matrix: list) -> list:
        # Execute the unvectorized code
        exec(code, globals())
        # Assuming the function name is "function", call it with the input matrix
        result = globals()["function"](input_matrix)
        return result

    def run_vectorized(self, code: str, input_matrix: list) -> list:
        # Execute the vectorized code
        exec(code, globals())
        # Assuming the function name is "function", call it with the input matrix
        result = globals()["function"](input_matrix)
        return result
