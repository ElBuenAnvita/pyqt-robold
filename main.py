import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit)
from PyQt6.QtCore import Qt

class BrazoRoboticoGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Brazo 6DOF - TinyBee")
        self.setFixedSize(400, 300)
        self.serial_port = None
        
        # --- INTERFAZ ---
        layout_principal = QVBoxLayout()
        
        # 1. Selector de Puertos COM
        layout_conexion = QHBoxLayout()
        self.combo_puertos = QComboBox()
        self.actualizar_puertos() # Llama a la función para buscar puertos
        
        self.btn_conectar = QPushButton("Conectar")
        self.btn_conectar.clicked.connect(self.conectar_serial)
        
        self.lbl_estado = QLabel("Desconectado")
        self.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
        
        layout_conexion.addWidget(self.combo_puertos)
        layout_conexion.addWidget(self.btn_conectar)
        layout_conexion.addWidget(self.lbl_estado)
        
        # 2. Control Motor X
        layout_motorX = QHBoxLayout()
        layout_motorX.addWidget(QLabel("Motor Base (X):"))
        self.input_x = QLineEdit("90") # Campo de texto con 90 por defecto
        
        self.btn_mover_x = QPushButton("Mover X")
        self.btn_mover_x.clicked.connect(self.mover_motor_x)
        
        layout_motorX.addWidget(self.input_x)
        layout_motorX.addWidget(self.btn_mover_x)
        
        # Ensamblar todo
        layout_principal.addLayout(layout_conexion)
        layout_principal.addLayout(layout_motorX)
        
        widget_central = QWidget()
        widget_central.setLayout(layout_principal)
        self.setCentralWidget(widget_central)

    # --- LÓGICA ---
    def actualizar_puertos(self):
        """Busca todos los puertos COM disponibles en Windows/Linux"""
        puertos = serial.tools.list_ports.comports()
        self.combo_puertos.clear()
        for puerto in puertos:
            self.combo_puertos.addItem(puerto.device) # ej. "COM4"

    def conectar_serial(self):
        if self.serial_port is None or not self.serial_port.is_open:
            puerto_seleccionado = self.combo_puertos.currentText()
            try:
                # Abrimos conexión a 115200 baudios
                self.serial_port = serial.Serial(puerto_seleccionado, 115200, timeout=1)
                self.lbl_estado.setText("Conectado")
                self.lbl_estado.setStyleSheet("color: green; font-weight: bold;")
                self.btn_conectar.setText("Desconectar")
            except Exception as e:
                self.lbl_estado.setText(f"Error: {str(e)}")
        else:
            # Desconectar
            self.serial_port.close()
            self.lbl_estado.setText("Desconectado")
            self.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
            self.btn_conectar.setText("Conectar")

    def mover_motor_x(self):
        """Traduce el input a G-Code y lo envía"""
        if self.serial_port and self.serial_port.is_open:
            try:
                grados = float(self.input_x.text())
                unidades = grados / 2  # Su conversión de 1mm = 2 grados
                
                # Armamos el string G-Code
                comando1 = "G91\n"
                comando2 = f"G1 X{unidades} F2000\n"
                
                # Enviamos al Marlin de la TinyBee
                self.serial_port.write(comando1.encode('utf-8'))
                self.serial_port.write(comando2.encode('utf-8'))
                print(f"Enviado: {comando2.strip()}")
            except ValueError:
                print("Por favor, ingrese un número válido.")
        else:
            print("Error: Puerto serial no conectado.")

# Arranque de la aplicación
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = BrazoRoboticoGUI()
    ventana.show()
    sys.exit(app.exec())