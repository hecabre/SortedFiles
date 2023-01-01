"""
@author: hecabre <aaroncabrera046@gmail.com>
"""
import customtkinter
import tkinter.messagebox
import os
import shutil
import sqlite3
import tkinter

# Connect to the 'extensions.db' SQLite database
conn = sqlite3.connect('extensions.db')
# Create a cursor to execute SQL commands
c = conn.cursor()
# Create the 'extensions' table if it does not exist
c.execute(
    '''
        CREATE TABLE IF NOT EXISTS extensions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            extension TEXT NOT NULL
        );
    '''
)

# Set the appearance mode to 'dark' and the default color theme to 'green' for the custom tkinter library
customtkinter.set_appearance_mode('dark')
customtkinter.set_default_color_theme('green')

# Store the current user's login name
SESSION = os.getlogin()
# Construct the path to the user's desktop
DESKTOP_PATH = f"C:/Users/{SESSION}/Desktop/"
# Construct the path to the user's downloads
DOWNLOAD_PATH = f"C:/Users/{SESSION}/Downloads"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title('Sorted Files')
        self.geometry(f"{450}x{500}")

        self.extension_entry = customtkinter.CTkEntry(
            master=self, placeholder_text='Type the extension', width=200)
        self.extension_entry.grid(row=0, column=0, padx=10, pady=10)
        self.extension_entry.focus()

        self.button_entry = customtkinter.CTkButton(
            master=self, text='Add extension', command=self.add_extension, width=200)
        self.button_entry.grid(row=0, column=1, pady=10)

        self.label_extension = customtkinter.CTkLabel(
            master=self, text='List of all extensions')
        self.label_extension.grid(row=1, column=0, sticky="nsew", columnspan=2)

        self.extension_frames = customtkinter.CTkFrame(master=self)
        self.extension_frames.grid(
            row=2, column=0, sticky="nsew", columnspan=2, padx=50)

        self.delete_files = customtkinter.CTkButton(
            master=self, text='Delete Files', command=self.delete_files_confirmation)
        self.delete_files.grid(row=3, column=0, padx=10, pady=10)

        self.btn_remove_all = customtkinter.CTkButton(
            master=self, text='Delete all extensions', command=self.delete_all_extensions)
        self.btn_remove_all.grid(row=3, column=1, padx=10, pady=10)

        self.bind('<Return>', lambda x: self.add_extension)

    def add_extension(self):
        """
        Add a file extension to the 'extensions' table.
        """
        # Retrieve the file extension from the input field
        name_extension = self.extension_entry.get()
        # Clear the input field
        self.extension_entry.delete(0, tkinter.END)
        # If the input field is not empty, add the file extension to the 'extensions' table
        if name_extension:
            # Add a leading dot to the file extension
            name_extension = f'.{name_extension}'
            # Insert the file extension into the 'extensions' table
            c.execute('''
                INSERT INTO extensions (extension) VALUES(?)
            ''', (name_extension,))
            # Save the changes to the database
            conn.commit()
            # Refresh the display of the extensions
            self.render_extensions()
        # If the input field is empty, show an error message
        else:
            tkinter.messagebox.showerror(
                'Sorted Files', 'Unable to add the extension, the entry is empty')

    def remove_extension(self, id):
        """Delete a row from the 'extensions' table and refresh the display of the extensions.

        Args:
            id (int): The id of the row to delete.
        """
        def _remove_extension():
            # Delete the row from the 'extensions' table
            c.execute("DELETE FROM extensions WHERE id = ?", (id,))
            # Save the changes to the database
            conn.commit()
            # Refresh the display of the extensions
            self.render_extensions()
        return _remove_extension

    def render_extensions(self):
        """
        Display a list of file extensions and allow the user to delete them.
        """
        # Retrieve all rows from the 'extensions' table
        self.rows = c.execute(
            '''
                SELECT * FROM extensions
            '''
        ).fetchall()

        # Destroy any existing widgets in the extension_frames frame
        for widget in self.extension_frames.winfo_children():
            widget.destroy()

        # Loop through the rows in the 'extensions' table
        for i in range(0, len(self.rows)):
            # Extract the id and file extension from the current row
            id = self.rows[i][0]
            self.extension = self.rows[i][2]
            # Display the file extension
            l_remove = customtkinter.CTkLabel(
                master=self.extension_frames, text=self.extension, width=100)
            l_remove.grid(row=i, column=0, pady=5)
            # Add a button to delete the file extension
            btn_remove = customtkinter.CTkButton(
                master=self.extension_frames, text='Delete extension {}'.format(self.extension), command=self.remove_extension(id), width=200)
            btn_remove.grid(row=i, column=1, pady=5)

    def delete_files_confirmation(self):
        """
        Ask the user for confirmation before deleting certain files.
        """
        # Prompt the user to enter a name for the folder that the sorted files will be moved to
        self.folder_name = customtkinter.CTkInputDialog(
            text='Write the name you want the folder to have', title='Sorted Files')
        # Store the user's input as the folder name
        self.folder_name = self.folder_name.get_input()

        # If the user entered a folder name, ask for confirmation before deleting the files
        if self.folder_name != '':
            self.msg_warning = tkinter.messagebox.askyesno(
                'Delete Files', 'Are you sure that you want to delete the files?')

            # If the user confirms, create a folder on the desktop and move and delete the relevant files
            if self.msg_warning:
                # Create a folder on the desktop
                self.file_path = self.create_desktop_folder()
                # Move and delete the relevant files
                self.delete_and_move_files(self.file_path)

        # If the user did not enter a folder name, show an error message
        else:
            tkinter.messagebox.showerror(
                title='Sorted Files', message='The input field is empty')

    def create_desktop_folder(self):
        '''
        Create a new folder on the desktop with the name of the users type
        :returns String returns name with the folder name that users type
        '''
        file_path = DESKTOP_PATH + str(self.folder_name)
        # Checks if exists that folder on the desktop
        if os.path.exists(file_path):
            tkinter.messagebox.showerror(
                title='Error', message='A folder with the name entered already exists')
        # Make the folder on the desktop
        else:
            print(file_path)
            os.makedirs(file_path)
            return file_path + '/'

    def delete_and_move_files(self, file_path):
        """Move and delete files with certain file extensions.

        Args:
            file_path (str): The destination path to move the files to.
        """
        rows = c.execute(
            '''
                SELECT * FROM extensions
            '''
        ).fetchall()  # Retrieve all rows from the 'extensions' table

        # Loop through the rows and move and delete the relevant files
        for extension in range(0, len(rows)):
            # Extract the file extension from the current row
            file_extension = rows[extension][2]
            # Construct the destination path for the current file extension
            path = file_path + file_extension

            # Create a directory at the destination path if it does not exist
            if not os.path.exists(path):
                os.mkdir(path)
            # Move and delete the relevant files
            self.move_files(file_extension, path)

    def move_files(self, file_extension, path):
        """Move and delete files with a specific file extension.

        Args:
            file_extension (str): The file extension to match.
            path (str): The destination path to move the files to.
        """
        for i in os.listdir(DOWNLOAD_PATH):         # Loop through the files in the DOWNLOAD_PATH directory
            # If a file ends with the specified file extension, move and delete
            if i.endswith(file_extension):
                # Construct the old and new file paths
                old_path = f'{DOWNLOAD_PATH}/{i}'
                new_path = f'{path}'
                try:
                    # Try to move the file and delete it from the old path
                    shutil.move(old_path, new_path)
                    os.remove(old_path)
                except Exception:
                    pass

    def delete_all_extensions(self):
        """Delete all rows from the 'extensions' table and refresh the display of the extensions.
        """
        # Loop through all rows in the 'extensions' table
        for i in range(0, len(self.rows)):
            # Extract the id of the current row
            id = self.rows[i][0]
            # Delete the row from the 'extensions' table
            c.execute("DELETE FROM extensions WHERE id = ?", (id,))
        # Save the changes to the database
        conn.commit()
        # Refresh the display of the extensions
        self.render_extensions()


if __name__ == "__main__":
    app = App()
    app.render_extensions()
    app.mainloop()
