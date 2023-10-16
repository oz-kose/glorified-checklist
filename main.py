import sys
import yaml
import re
import qdarktheme
from PyQt5.QtWidgets import QTabWidget, QApplication, QFileDialog, QTextEdit, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QListWidget, QCheckBox, QLineEdit, QPushButton, QListWidgetItem
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load steps from the default YAML file
        with open("steps.yaml", 'r') as file:
            data = yaml.safe_load(file)

        self.steps = data["steps"]
        self.sub_step_descriptions = data["sub_step_descriptions"]
        self.load_steps_and_descriptions_from_yaml("steps.yaml")

        # Auto-save every second (1000 ms)
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(1000)  # time in milliseconds

        # Initialize stuff
        self.checkbox_states = {main_step: [False]*len(sub_steps) for main_step, sub_steps in self.steps.items()}
        self.main_step_items = []
        self.sys_var = ""
        self.rack_var = ""
        self.plain_rack_var = ""
        self.mtor_var = ""
        self.tor_var = ""
        self.pdu_var = ""
        self.bmc_var = ""
        self.server_var = ""
        self.sr_var = ""
        self.user_notes = {}
        self.current_step_name = None
        self.text_edit = QTextEdit()
        self.env_text_edit = QTextEdit()
        # self.env_text_edit2 = QTextEdit()
        self.host_text_edit = QTextEdit()
        self.mtm_var = ["SYS-2049U-TR4", "SR650", "NF5488M5"]
        self.info_yaml_str = ""
        self.bmc_yaml_str = ""
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle('xCat Checklist')

        # Create the tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        
        # Add tabs to the widget
        self.tab_widget.addTab(self.tab1, "Checklist")
        self.tab_widget.addTab(self.tab2, "vi Generator")
        
        # Add contents to the first tab
        self.configure_main_steps_tab()
        
        # Add contents to the second tab
        self.configure_tab2()
        
        self.setCentralWidget(self.tab_widget)

    def configure_main_steps_tab(self):
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

        # Input and button line
        self.sys_input = QLineEdit(self)
        self.rack_input = QLineEdit(self)
        self.mtm_input = QComboBox(self)
        self.sys_label = QLabel("SYS-JIRA: ", self)
        self.rack_label = QLabel("Full Rack Name: ", self)
        self.mtm_label = QLabel("MTM: ", self)
        self.mtm_input.addItems(self.mtm_var)
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
        self.user_input_text.textChanged.connect(self.update_user_note)

        layout_right_v.addLayout(layout_top_h)
        layout_right_v.addWidget(self.sub_steps_widget)
        layout_right_v.addLayout(self.sub_step_detail_layout)
    
        layout_h.addLayout(layout_left_v, 1)
        layout_h.addLayout(layout_right_v, 3)

        central_widget = QWidget()
        central_widget.setLayout(layout_h)
        self.setCentralWidget(central_widget)
        self.tab1.setLayout(layout_h)

    def configure_tab2(self):
        layout = QVBoxLayout(self.tab2)
        
        self.sub_tab_widget = QTabWidget(self.tab2)
        layout.addWidget(self.sub_tab_widget)

        sub_tab = QWidget()
        self.configure_input_sub_tab(sub_tab)
        self.sub_tab_widget.addTab(sub_tab, "Input")

        sub_tab = QWidget()
        self.configure_envvar_sub_tab(sub_tab)
        self.sub_tab_widget.addTab(sub_tab, "env var")

        sub_tab = QWidget()
        self.configure_info_sub_tab(sub_tab)
        self.sub_tab_widget.addTab(sub_tab, f"{self.rack_var}-info.yaml")

        sub_tab = QWidget()
        self.configure_host_sub_tab(sub_tab)
        self.sub_tab_widget.addTab(sub_tab, f"{self.plain_rack_var}.txt")

        sub_tab = QWidget()
        self.configure_bmc_sub_tab(sub_tab)
        self.sub_tab_widget.addTab(sub_tab, f"{self.plain_rack_var}bmc.txt")

################################## TAB 1 ##################################

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
        self.sys_var = self.sys_input.text()
        self.rack_var = self.rack_input.text()
        self.mtm_var = self.mtm_input.currentText()
        self.plain_rack_var = re.search(r'rk\d+', self.rack_var).group(0) if re.search(r'rk\d+', self.rack_var) else None
        self.plain_sr_var = re.search(r'sr\d+', self.rack_var).group(0) if re.search(r'sr\d+', self.rack_var) else None

        match = re.search(r'rk(\d+)', self.rack_var)
        match_sr = re.search(r'sr(\d+)', self.rack_var)

        if match:
            r_value = match.group(1)
            self.mtor_var = f'r{r_value}-mtor'
            self.tor_var = f'r{r_value}-tor'
            self.pdu_var = f'r{r_value}pdu'
            self.bmc_var = f'r{r_value}bmc'
            self.server_var = f'r{r_value}s'

        if match_sr:
            sr_value = match.group(1)
            self.sr_var = f'r{sr_value}s'

        self.update_tab2()

    def load_steps_and_descriptions_from_yaml(self, file_path):
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        
        self.steps = data.get('steps', {})
        self.sub_step_descriptions = data.get('sub_step_descriptions', {})

    def auto_save(self):
        try:
            save_data = self.create_save_data()
            yaml_str = self.serialize_save_data(save_data)
            filename = "delete-me-autosave.yaml"
            self.save_to_file(yaml_str, filename)
        except Exception as e:
            print(f"Auto-save failed: {str(e)}")

    def closeEvent(self, event):
        # Add logic here if you want to ask the user to confirm quitting.
        
        # Save the current state
        self.auto_save()
        
        # Accept the event which will close the app
        event.accept()


    def display_sub_step_detail(self, step_name):
        # Fetch and format the predefined text
        predef_text = self.sub_step_descriptions.get(step_name, "")
        modified_text = predef_text.format(sys=self.sys_var, rack=self.rack_var, mtm=self.mtm_var, 
                                        plain_rack=self.plain_rack_var, mtor=self.mtor_var, tor=self.tor_var, 
                                        pdu=self.pdu_var, bmc=self.bmc_var, server=self.server_var)
        
        # Add predefined details
        self.sub_step_detail_text.setPlainText(modified_text)

        # Update the current step name
        self.current_step_name = step_name
        user_note_widget = self.user_notes.get(step_name)
        if user_note_widget is not None:
            user_note = self.user_notes.get(step_name, "")
            self.user_input_text.setPlainText(user_note)
        else:
            user_note = ""

        self.user_input_text.setPlainText(user_note)
        
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
            'user_notes': self.user_notes,
            'checkbox_states': self.checkbox_states,
            'info_yaml' : self.info_yaml_str,
            'bmc_yaml' : self.bmc_yaml_str
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
        filename, _ = QFileDialog.getOpenFileName(self, "Load session", "", "YAML Files (*.yaml)")
        if filename:
            self.load_session_from_file(filename)

    def update_user_note(self):
        if self.current_step_name is not None:
            self.user_notes[self.current_step_name] = self.user_input_text.toPlainText()
            print(f"Updated note for {self.current_step_name}: {self.user_notes[self.current_step_name]}")

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
            self.user_notes = loaded_user_notes  # Since these are plain strings, no need for QTextEdits here
            self.checkbox_states = data.get('checkbox_states', {})
            self.info_yaml_str = data.get('info_yaml', "")
            self.bmc_yaml_str = data.get('bmc_yaml', "")

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

            for step_name, note in loaded_user_notes.items():
                if step_name in self.user_notes:
                    self.user_notes[step_name].setPlainText(note)
                else:
                    text_edit = QTextEdit(self)
                    text_edit.setPlainText(note)
                    self.user_notes[step_name] = text_edit

            current_item = self.main_steps_view.currentItem()
            if current_item:
                self.on_main_step_clicked(current_item)
                    
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
        except yaml.YAMLError as ye:
            print(f"Error parsing YAML file {filename}: {str(ye)}")
        except Exception as e:
            print(f"Unexpected error loading session from {filename}: {str(e)}")

        self.update_tab2()
        self.configure_envvar_sub_tab(self)

################################## TAB 1 ##################################
################################## TAB 2 ##################################

    def update_tab2(self):
        # Update tab names based on new variable values
        self.sub_tab_widget.setTabText(2, f"{self.rack_var}-info.yaml")
        self.sub_tab_widget.setTabText(3, f"{self.plain_rack_var}.txt")
        self.sub_tab_widget.setTabText(4, f"{self.plain_rack_var}bmc.txt")
        self.update_env_text_edit()
        # self.update_env_text_edit2()
        self.update_host_text_edit()
        self.bmc_output_text_edit.setText(self.bmc_yaml_str)
        self.info_output_text_edit.setText(self.info_yaml_str)

    def configure_input_sub_tab(self, sub_tab):
        layout_v = QVBoxLayout(sub_tab)

        # Vertical layout for MAC
        layout_v_mac = QVBoxLayout()
        
        # Add a "MAC" label
        mac_label = QLabel("MAC:", self)
        layout_v_mac.addWidget(mac_label)

        # Add text input box for "MAC"
        self.mac_input = QTextEdit(self)
        layout_v_mac.addWidget(self.mac_input)

        # Vertical layout for PW
        layout_v_pw = QVBoxLayout()

        # Add a "PW" label
        pw_label = QLabel("PW:", self)
        layout_v_pw.addWidget(pw_label)

        # Add text input box for "PW"
        self.pw_input = QTextEdit(self)
        layout_v_pw.addWidget(self.pw_input)

        # Horizontal layout for text boxes
        layout_h_text = QHBoxLayout()
        layout_h_text.addLayout(layout_v_mac)
        layout_h_text.addLayout(layout_v_pw)

        # Horizontal layout for buttons
        layout_h_buttons = QHBoxLayout()

        # Add a "Save" button
        save_button = QPushButton("Save", self)
        layout_h_buttons.addWidget(save_button)

        # Add a "Clear" button
        clear_button = QPushButton("Clear", self)
        layout_h_buttons.addWidget(clear_button)

        # Connect the buttons to their respective slots
        save_button.clicked.connect(self.save_text)
        clear_button.clicked.connect(self.clear_text)

        # Add horizontal layouts to the vertical layout
        layout_v.addLayout(layout_h_text)
        layout_v.addLayout(layout_h_buttons)
        sub_tab.setLayout(layout_v)

    def save_text(self):
        # Retrieve text from the input boxes and save/process it as needed
        macs = self.mac_input.toPlainText().split('\n')
        pws = self.pw_input.toPlainText().split('\n')
        hosts = self.host_text_edit.toPlainText().split('\n')
        reversed_hosts = hosts[::-1]
        mtms = self.mtm_input.currentText()
        data = {}
        clean_macs = [self.format_mac(mac) for mac in macs if len(mac.strip()) >= 5]
        clean_pws = [pw.strip().replace('"', '').replace('\'', '').replace('\n', '') for pw in pws if len(pw.strip()) >= 5]

        for host, mac, pw in zip(reversed_hosts, clean_macs, clean_pws):
            key = f"{host}-bmc"
            data[key] = {
                'mac': mac,
                'password': pw,
                'mtm': mtms,
            }

        sorted_data = {k: data[k] for k in sorted(data, reverse=True)}
        self.info_yaml_str = yaml.dump(sorted_data, sort_keys=False)  # 'sort_keys=False' is important to preserve order in YAML
        self.info_output_text_edit.setText(self.info_yaml_str)

        bmc_data = {'bmc': {}}
        for host, pw in zip(reversed_hosts, clean_pws):
            bmc_data['bmc'][host] = {
                'vendor_password': pw
            }

        self.bmc_yaml_str = yaml.dump(bmc_data)
        self.bmc_output_text_edit.setText(self.bmc_yaml_str)

    def format_mac(self, mac):
        mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
        if len(mac) != 12:
            return 'INVALID'  # or some other form of error indication
        return ':'.join(mac[i:i+2] for i in range(0, len(mac), 2))

    def clear_text(self):
        # Clear the input boxes
        self.mac_input.clear()
        self.pw_input.clear()

    def configure_envvar_sub_tab(self, sub_tab):
        main_layout = QVBoxLayout(sub_tab)
        hbox_layout = QHBoxLayout()

        left_vbox_layout = QVBoxLayout()
        right_vbox_layout = QVBoxLayout()

        self.env_text_edit.setReadOnly(True)
        self.update_env_text_edit()
        left_vbox_layout.addWidget(self.env_text_edit)

        # self.env_text_edit2.setReadOnly(True)
        # self.update_env_text_edit2()
        # right_vbox_layout.addWidget(self.env_text_edit2)

        hbox_layout.addLayout(left_vbox_layout)
        hbox_layout.addLayout(right_vbox_layout)

        hbox_layout.setStretchFactor(left_vbox_layout, 1)
        hbox_layout.setStretchFactor(right_vbox_layout, 1)

        main_layout.addLayout(hbox_layout)
        sub_tab.setLayout(main_layout)

    def update_env_text_edit(self):
        # Update text_edit text based on variable values
        self.env_text_edit.setText(f"""export {self.mtor_var}
export {self.tor_var}
export {self.pdu_var}
export {self.bmc_var}
export {self.server_var}
""")
        
#     def update_env_text_edit2(self):
#         # Update text_edit text based on variable values
#         self.env_text_edit2.setText(f"""export {self.sr_var}{self.mtor_var}
# export {self.sr_var}{self.tor_var}
# export {self.sr_var}{self.pdu_var}
# export {self.sr_var}{self.bmc_var}
# export {self.sr_var}{self.server_var}
# """)

    def configure_info_sub_tab(self, sub_tab):
        layout = QVBoxLayout(sub_tab)
        self.info_output_text_edit = QTextEdit(self)
        self.info_output_text_edit.setReadOnly(True)
        layout.addWidget(self.info_output_text_edit)
        sub_tab.setLayout(layout)

    def configure_host_sub_tab(self, sub_tab):
        layout = QVBoxLayout(sub_tab)
        self.host_text_edit.setReadOnly(True)
        self.update_host_text_edit()
        layout.addWidget(self.host_text_edit)

    def update_host_text_edit(self):
        excluded = {22, 24, 26}
        output_servers = []

        for i in range(2, 51, 2):
            if i in excluded:
                continue
            output_servers.append(f"{self.rack_var}-s{i:02d}")
            if len(output_servers) == 22:
                break
        
        output_text = "\n".join(output_servers)
        self.host_text_edit.setText(output_text)

    def configure_bmc_sub_tab(self, sub_tab):
        layout = QVBoxLayout(sub_tab)
        self.bmc_output_text_edit = QTextEdit(self)
        self.bmc_output_text_edit.setReadOnly(True)
        layout.addWidget(self.bmc_output_text_edit)
        sub_tab.setLayout(layout)

################################## TAB 2 ##################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    font = QFont("Lucida Sans", 9)
    app.setFont(font)
    ex = MyApp()
    ex.showMaximized()
    sys.exit(app.exec_())
