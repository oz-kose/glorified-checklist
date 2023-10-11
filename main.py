import sys
import yaml
import re
import qdarktheme
from PyQt5.QtWidgets import QApplication, QTextEdit, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QCheckBox, QLineEdit, QPushButton, QListWidgetItem
from PyQt5.QtGui import QFont

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load steps from YAML file
        with open("steps.yaml", 'r') as file:
            data = yaml.safe_load(file)

        self.steps = data["steps"]
        self.sub_step_descriptions = data["sub_step_descriptions"]

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

        self.initUI()

    def initUI(self):
        self.setWindowTitle('MyApp')

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
        self.save_button = QPushButton("Save", self)
        self.load_button = QPushButton("Load", self)

        layout_top_h = QHBoxLayout()
        layout_top_h.addWidget(self.sys_label)
        layout_top_h.addWidget(self.sys_input)
        layout_top_h.addWidget(self.rack_label)
        layout_top_h.addWidget(self.rack_input)
        layout_top_h.addWidget(self.mtm_label)
        layout_top_h.addWidget(self.mtm_input)
        layout_top_h.addWidget(self.confirm_button)
        self.confirm_button.clicked.connect(self.confirm_inputs)
        layout_top_h.addWidget(self.save_button)
        layout_top_h.addWidget(self.load_button)

        layout_right_v.addLayout(layout_top_h)

        # Right pane for sub steps
        self.sub_steps_widget = QWidget()
        self.sub_steps_layout = QVBoxLayout()
        self.sub_steps_widget.setLayout(self.sub_steps_layout)

        # Add a QTextEdit widget to show sub-step details
        self.sub_step_detail_text = QTextEdit()
        self.sub_step_detail_text.setReadOnly(True)  # Make it read-only
        layout_right_v.addWidget(self.sub_steps_widget)
        layout_right_v.addWidget(self.sub_step_detail_text)  # Add to the layout


        layout_right_v.addWidget(self.sub_steps_widget)

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

    def display_sub_step_detail(self, step_name):
        """Slot to handle sub-step checkbox clicks."""
        # Fetch the predefined text
        predef_text = self.sub_step_descriptions.get(step_name, "")
        
        # Replace placeholders with variable values
        modified_text = predef_text.format(sys=self.sys_var, rack=self.rack_var, plain_rack=self.plain_rack_var, mtm=self.mtm_var, mtor=self.mtor_var, tor=self.tor_var, pdu=self.pdu_var, bmc=self.bmc_var, server=self.server_var)
        
        # Update the QTextEdit with the modified text
        self.sub_step_detail_text.setPlainText(modified_text)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    font = QFont("Lucida Sans", 9)
    app.setFont(font)
    ex = MyApp()
    ex.showMaximized()
    sys.exit(app.exec_())
