import subprocess
import time

# List of input files and output files
input_files = ["input_easy1.txt", "input_easy2.txt", "input_hard2.txt", "input_medium1.txt", "input_medium2.txt",
               "input_impossible1.txt", "input_impossible2.txt", "input_impossible3.txt"]

# Run checkers_starter.py for each combination of input and output files
for i in range(0, len(input_files)):
    input_file = input_files[i]
    output_file = input_file.replace("input", "output")
    solution_file = input_file.replace("input", "solution")

    # Measure the execution time
    start_time = time.time()

    # Run the checkers_starter.py script with the given input and output files
    command = f"python battle.py --inputfile {input_file} --outputfile {output_file}"
    subprocess.run(command, shell=True)

    # Calculate and print the time taken
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execution time for {input_file}: {elapsed_time} seconds")
    output_file_reader = open(output_file, "r")
    solution_file_reader = open(solution_file, "r")
    if output_file_reader.read().splitlines() == solution_file_reader.read().splitlines():
        print("Correct")
    else:
        print("Incorrect")
        print("Output")
        output_file = open(output_file, "r")
        print(output_file.read())
        print("Solution")
        solution_file = open(solution_file, "r")
        print(solution_file.read())


