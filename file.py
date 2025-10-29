#f = open("file.txt","r", encodings="utf-8")
# r = read
# w = write
# a = append
# x = create

# Import the datetime class from the datetime module
from datetime import datetime, timedelta


# Define a custom exception for duplicate visitors
class DuplicateVisitorError(Exception):
    def __init__(self, name):
        # Set a custom message if a visitor tries to sign in twice in a row
        self.message = f"Visitor '{name}' already signed in last! No back to back visits allowed."
        # Call the base Exception class with this message
        super().__init__(self.message)


class RecentVisitorError(Exception):
    def __init__(self, name):
        self.message = f"Visitor '{name}' is not allowed to sign in yet. Please try again in 5 minutes."
        super().__init__(self.message)


# Define the main function that runs the program
def main():
    # The name of the file where the visitor records are stored
    filename = "visitors.txt"

    # Ensure the file exists before we start using it
    try:
        # Try opening the file in read mode
        with open(filename, "r", encoding="utf-8") as f:
            pass  # Do nothing, just check if file exists
    except FileNotFoundError:
        # If file does not exist, create the file by opening in write mode
        print("file not found, creating a new file")
        with open(filename, "w", encoding="utf-8") as f:
            pass  # Just create a new line

    # Ask the user to type the visitor's name
    visitor = input("Enter visitor's name: ")

    try:
        # Open the file to read the existing visitors' records
        with open(filename, "r", encoding="utf-8") as f:
            # Read all lines into a list
            lines = f.readlines()
            # Get the name of the last visitor

            if lines:
                last_line = lines[-1].strip()
                last_visitor, last_time = last_line.split(" | ")
                last_visit_time = datetime.fromisoformat(last_time)
            else:
                last_visitor, last_time = None, None

                # Check if the new visitor is the same as last
                if visitor == last_visitor:
                    # If yes, raise our custom DuplicateVisitorError
                    raise DuplicateVisitorError(visitor)
                if last_time:
                   now = datetime.now()
                   time_diff = now - last_time
                if time_diff < timedelta(minutes=5):
                    raise RecentVisitorError(last_visitor)

        # If not a duplicate, open the file in append mode
        with open(filename, "a", encoding="utf-8") as f:
            # write the visitor's name and the current date and time
            f.write(f"{visitor} | {datetime.now()}\n")

        # Tell the user everything worked fine
        print("Visitor added successfully!")

    # Catch the custom error if a duplicate user was detected
    except DuplicateVisitorError as e:
        # Print out the error message
        print("Error:", e)

    except RecentVisitorError as e:
        print("Error:", e)


# Run the program
main()





