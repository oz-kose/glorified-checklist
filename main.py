import sys
import yaml
import re
import qdarktheme
from PyQt5.QtWidgets import QApplication, QFileDialog, QTextEdit, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QCheckBox, QLineEdit, QPushButton, QListWidgetItem
from PyQt5.QtGui import QFont

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load steps from YAML file
        with open("steps.yaml", 'r') as file:
            data = yaml.safe_load(file)

        self.steps = data["steps"]
        self.sub_step_descriptions = data["sub_step_descriptions"]
        self.load_steps_and_descriptions_from_yaml("steps.yaml")

        # Initialize stuff
        self.checkbox_states = {main_step: [False]*len(sub_steps) for main_step, sub_steps in self.steps.items()}
        self.main_step_items = []
        self.sys_var = ""
        self.rack_var = ""
        self.plain_rack_var = ""
        self.mtm_var = ""
        self.mtor_var = ""
        self.tor_var = ""
        self.pdu_var = ""
        self.bmc_var = ""
        self.server_var = ""
        self.user_notes = {}
        self.current_step_name = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle('xCat Checklist')

        layout_h = QHBoxLayout()
        layout_left_v = QVBoxLayout()
        layout_right_v = QVBoxLayout()

        # Left pane with list of main steps
        self.main_steps_view = QListWidget()
        for main_step in self.steps:
            item = QListWidgetItem(main_step)
            self.main_steps_view.addItem(item)
            self.main_step_items.append(item)
        
        self.main_steps_view.itemClicked.connect(self.on_main_step_clicked)
        layout_left_v.addWidget(self.main_steps_view)

        # Line edits and buttons
        self.sys_input = QLineEdit(self)
        self.rack_input = QLineEdit(self)
        self.mtm_input = QLineEdit(self)
        self.sys_label = QLabel("Sys-JIRA: ", self)
        self.rack_label = QLabel("Full Rack Name: ", self)
        self.mtm_label = QLabel("MTM: ", self)
        self.confirm_button = QPushButton("Confirm", self)
        self.confirm_button.clicked.connect(self.confirm_inputs)
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_button_clicked)
        self.load_button = QPushButton("Load", self)
        self.load_button.clicked.connect(self.load_button_clicked)
        
        layout_top_h = QHBoxLayout()
        layout_top_h.addWidget(self.sys_label)
        layout_top_h.addWidget(self.sys_input)
        layout_top_h.addWidget(self.rack_label)
        layout_top_h.addWidget(self.rack_input)
        layout_top_h.addWidget(self.mtm_label)
        layout_top_h.addWidget(self.mtm_input)
        layout_top_h.addWidget(self.confirm_button)
        layout_top_h.addWidget(self.save_button)
        layout_top_h.addWidget(self.load_button)

        # Right pane for sub steps
        self.sub_steps_widget = QWidget()
        self.sub_steps_layout = QVBoxLayout()
        self.sub_steps_widget.setLayout(self.sub_steps_layout)
        self.sub_step_detail_layout = QVBoxLayout()

        # Pre-create the QTextEdit widgets and add them to sub_step_detail_layout
        self.sub_step_detail_text = QTextEdit()
        self.sub_step_detail_text.setReadOnly(True)
        self.sub_step_detail_layout.addWidget(self.sub_step_detail_text)
        
        self.user_input_text = QTextEdit()
        self.user_input_text.setPlaceholderText("Your notes here...")
        self.sub_step_detail_layout.addWidget(self.user_input_text)

        layout_right_v.addLayout(layout_top_h)
        layout_right_v.addWidget(self.sub_steps_widget)
        layout_right_v.addLayout(self.sub_step_detail_layout)
    
        layout_h.addLayout(layout_left_v, 1)
        layout_h.addLayout(layout_right_v, 3)

        central_widget = QWidget()
        central_widget.setLayout(layout_h)
        self.setCentralWidget(central_widget)


    def on_main_step_clicked(self, item):
        # Clear the current sub steps
        while self.sub_steps_layout.count():
            child = self.sub_steps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Display the new sub steps
        main_step_name = item.text()
        main_step = self.steps[main_step_name]
        chk_states = self.checkbox_states[main_step_name]

        for i, sub_step in enumerate(main_step):
            chk_box = QCheckBox(sub_step)
            chk_box.setChecked(chk_states[i])
            chk_box.stateChanged.connect(lambda state, main_step=main_step_name, idx=i: self.on_checkbox_state_changed(main_step, idx, state))
            chk_box.clicked.connect(lambda _, step=sub_step: self.display_sub_step_detail(step))  # Connect click event
            self.sub_steps_layout.addWidget(chk_box)

        self.sub_steps_layout.addStretch()

    def on_checkbox_state_changed(self, main_step, index, state):
        """Slot for checkbox state changed signal."""
        self.checkbox_states[main_step][index] = bool(state)

        # Check if all checkboxes for this main step are checked
        if all(self.checkbox_states[main_step]):
            font = self.main_step_items[list(self.steps.keys()).index(main_step)].font()
            font.setStrikeOut(True)
            self.main_step_items[list(self.steps.keys()).index(main_step)].setFont(font)
        else:
            font = self.main_step_items[list(self.steps.keys()).index(main_step)].font()
            font.setStrikeOut(False)
            self.main_step_items[list(self.steps.keys()).index(main_step)].setFont(font)
        
    def confirm_inputs(self):
        """Slot to handle Confirm button clicks."""
        self.sys_var = self.sys_input.text()
        self.rack_var = self.rack_input.text()
        self.mtm_var = self.mtm_input.text()
        self.plain_rack_var = re.search(r'rk\d+', self.rack_var).group(0) if re.search(r'rk\d+', self.rack_var) else None

        match = re.search(r'rk(\d+)', self.rack_var)

        if match:
            r_value = match.group(1)
            self.mtor_var = f'r{r_value}-mtor'
            self.tor_var = f'r{r_value}-tor'
            self.pdu_var = f'r{r_value}pdu'
            self.bmc_var = f'r{r_value}bmc'
            self.server_var = f'r{r_value}s'

    def load_steps_and_descriptions_from_yaml(self, file_path):
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        
        self.steps = data.get('steps', {})
        self.sub_step_descriptions = data.get('sub_step_descriptions', {})

    def display_sub_step_detail(self, step_name):
        # Fetch and format the predefined text
        predef_text = self.sub_step_descriptions.get(step_name, "")
        modified_text = predef_text.format(sys=self.sys_var, rack=self.rack_var, mtm=self.mtm_var, 
                                        plain_rack=self.plain_rack_var, mtor=self.mtor_var, tor=self.tor_var, 
                                        pdu=self.pdu_var, bmc=self.bmc_var, server=self.server_var)
        
        # Add predefined details
        self.sub_step_detail_text.setPlainText(modified_text)

        user_note_widget = self.user_notes.get(step_name)
        if user_note_widget is not None:
            user_note = user_note_widget.toPlainText()
        else:
            user_note = ""

        self.user_input_text.setPlainText(user_note)
        
        # Update the current step name
        self.current_step_name = step_name

    def create_save_data(self):
        save_data = {
            'sys_var': self.sys_var,
            'rack_var': self.rack_var,
            'mtm_var': self.mtm_var,
            'plain_rack_var' : self.plain_rack_var,
            'mtor_var' : self.mtor_var,
            'tor_var' : self.tor_var,
            'pdu_var' : self.pdu_var,
            'bmc_var' : self.bmc_var,
            'server_var' : self.server_var,
            'steps': self.steps,
            'user_notes': {step_name: text_edit.toPlainText() for step_name, text_edit in self.user_notes.items()},
            'checkbox_states': self.checkbox_states
            # Add more data when there's new stuff
        }
        return save_data

    def serialize_save_data(self, save_data):
        return yaml.dump(save_data)

    def save_to_file(self, yaml_str, filename):
        with open(filename, 'w') as file:
            file.write(yaml_str)

    def save_button_clicked(self):
        save_data = self.create_save_data()
        yaml_str = self.serialize_save_data(save_data)
        filename = f"{self.sys_var}-{self.rack_var}.yaml"
        self.save_to_file(yaml_str, filename)

    def load_button_clicked(self):
        # You may use QFileDialog to get the filename to load
        filename, _ = QFileDialog.getOpenFileName(self, "Load session", "", "YAML Files (*.yaml)")
        if filename:
            self.load_session_from_file(filename)

    def load_session_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                data = yaml.safe_load(file)

            # Apply loaded settings
            self.sys_var = data.get('sys_var', "")
            self.rack_var = data.get('rack_var', "")
            self.mtm_var = data.get('mtm_var', "")
            self.plain_rack_var = data.get('plain_rack_var', "")
            self.mtor_var = data.get('mtor_var', "")
            self.tor_var = data.get('tor_var', "")
            self.pdu_var = data.get('pdu_var', "")
            self.bmc_var = data.get('bmc_var', "")
            self.server_var = data.get('server_var', "")
            loaded_user_notes = data.get('user_notes', {})
            self.user_notes = {}
            self.checkbox_states = data.get('checkbox_states', {})

            # Assume 'main_step_name' is correctly acquired from UI or data. Otherwise, modify as needed.
            main_step_name = (
                self.main_steps_view.currentItem().text() 
                if self.main_steps_view.currentItem() 
                else None
            )
            if main_step_name:
                # Regenerate sub-steps UI to reflect loaded checkbox states
                self.on_main_step_clicked(self.main_steps_view.currentItem())
                
            # Update UI Elements with Loaded Data
            self.sys_input.setText(self.sys_var)
            self.rack_input.setText(self.rack_var)
            self.mtm_input.setText(self.mtm_var)

            for step_name, note in loaded_user_notes.items():
                if step_name in self.user_notes:
                    # If there's already a QTextEdit for this step, update its content
                    self.user_notes[step_name].setPlainText(note)
                else:
                    # Otherwise, create a new QTextEdit, set its content, and store it in the dictionary for future reference
                    text_edit = QTextEdit(self)
                    text_edit.setPlainText(note)
                    self.user_notes[step_name] = text_edit
                    
                    # Ensure the new QTextEdit is properly added to your UI
                    # E.g., self.sub_step_detail_layout.addWidget(text_edit)



            current_item = self.main_steps_view.currentItem()
            if current_item:
                self.on_main_step_clicked(current_item)
                    
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
            # Optionally: Display a user-friendly error message in your GUI.
        except yaml.YAMLError as ye:
            print(f"Error parsing YAML file {filename}: {str(ye)}")
            # Optionally: Display a user-friendly error message in your GUI.
        except Exception as e:
            print(f"Unexpected error loading session from {filename}: {str(e)}")
            # Optionally: Display a user-friendly error message in your GUI.



if __name__ == '__main__':
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    font = QFont("Lucida Sans", 9)
    app.setFont(font)
    ex = MyApp()
    ex.showMaximized()
    sys.exit(app.exec_())
