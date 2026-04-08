import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QSlider)
from PyQt6.QtCore import Qt

class BrazoRoboticoGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Brazo 6DOF - TinyBee")
        self.setFixedSize(450, 480) # Ventana un poco más alta para los nuevos controles
        self.serial_port = None
        
        self.inputs = {}
        
        # --- INTERFAZ ---
        layout_principal = QVBoxLayout()
        
        # 1. Selector de Puertos COM
        layout_conexion = QHBoxLayout()
        self.combo_puertos = QComboBox()
        self.actualizar_puertos()
        
        self.btn_conectar = QPushButton("Conectar")
        self.btn_conectar.clicked.connect(self.conectar_serial)
        
        self.lbl_estado = QLabel("Desconectado")
        self.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
        
        layout_conexion.addWidget(self.combo_puertos)
        layout_conexion.addWidget(self.btn_conectar)
        layout_conexion.addWidget(self.lbl_estado)
        layout_principal.addLayout(layout_conexion)
        
        # 2. Creación dinámica de los controles para los 6 ejes
        ejes = [
            ("Base (T)", "T", "90"),
            ("Hombro (X)", "X", "90"),
            ("Codo (Y)", "Y", "90"),
            ("Muñeca 1 (E)", "E", "90"),
            ("Muñeca 2 (Z)", "Z", "90"),
            ("Garra (Servo)", "Servo", "180")
        ]
        
        for nombre, eje_id, val_defecto in ejes:
            layout_principal.addLayout(self.crear_fila_motor(nombre, eje_id, val_defecto))
            
        # 3. Control de Velocidad (Slider)
        layout_velocidad = QHBoxLayout()
        layout_velocidad.addWidget(QLabel("Velocidad Global:"))
        
        self.slider_velocidad = QSlider(Qt.Orientation.Horizontal)
        self.slider_velocidad.setRange(10, 100) # Rango de 10% a 100%
        self.slider_velocidad.setValue(100) # Inicia al 100%
        self.slider_velocidad.valueChanged.connect(self.cambiar_velocidad)
        
        self.lbl_velocidad_val = QLabel("100%")
        
        layout_velocidad.addWidget(self.slider_velocidad)
        layout_velocidad.addWidget(self.lbl_velocidad_val)
        layout_principal.addLayout(layout_velocidad)
        
        # 4. Botones de Sistema (Límites y Emergencia)
        layout_sistema = QHBoxLayout()
        
        self.btn_fijar_cero = QPushButton("Fijar Cero (Quitar Límites)")
        self.btn_fijar_cero.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        self.btn_fijar_cero.clicked.connect(self.fijar_cero_y_limites)
        
        self.btn_stop = QPushButton("¡Detener Servo (S-1)!")
        self.btn_stop.setStyleSheet("background-color: #ff4c4c; color: white; font-weight: bold; padding: 5px;")
        self.btn_stop.clicked.connect(self.detener_servo)
        
        layout_sistema.addWidget(self.btn_fijar_cero)
        layout_sistema.addWidget(self.btn_stop)
        layout_principal.addLayout(layout_sistema)

        # Ensamblar todo en la ventana
        widget_central = QWidget()
        widget_central.setLayout(layout_principal)
        self.setCentralWidget(widget_central)

    # --- FUNCIONES DE CREACIÓN DE UI ---
    def crear_fila_motor(self, nombre, eje_id, val_defecto):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"Motor {nombre}:"))
        input_val = QLineEdit(val_defecto)
        self.inputs[eje_id] = input_val 
        btn_mover = QPushButton(f"Mover {eje_id}")
        btn_mover.clicked.connect(lambda checked, e=eje_id: self.mover_motor(e))
        layout.addWidget(input_val)
        layout.addWidget(btn_mover)
        return layout

    # --- LÓGICA SERIAL ---
    def actualizar_puertos(self):
        puertos = serial.tools.list_ports.comports()
        self.combo_puertos.clear()
        for puerto in puertos:
            self.combo_puertos.addItem(puerto.device)

    def conectar_serial(self):
        if self.serial_port is None or not self.serial_port.is_open:
            puerto_seleccionado = self.combo_puertos.currentText()
            try:
                self.serial_port = serial.Serial(puerto_seleccionado, 115200, timeout=1)
                self.lbl_estado.setText("Conectado")
                self.lbl_estado.setStyleSheet("color: green; font-weight: bold;")
                self.btn_conectar.setText("Desconectar")
            except Exception as e:
                self.lbl_estado.setText(f"Error: {str(e)}")
        else:
            self.serial_port.close()
            self.lbl_estado.setText("Desconectado")
            self.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
            self.btn_conectar.setText("Conectar")

    def mover_motor(self, eje_id):
        if not (self.serial_port and self.serial_port.is_open):
            print("Error: Puerto serial no conectado.")
            return
        
        try:
            valor = float(self.inputs[eje_id].text())
            if eje_id == "Servo":
                comando = f"M280 P0 S{valor}\n"
                self.serial_port.write(comando.encode('utf-8'))
                print(f"Enviado a Garra: {comando.strip()}")
                return

            unidades = valor / 2
            self.serial_port.write("G91\n".encode('utf-8')) 
            
            if eje_id == "T":
                self.serial_port.write("T0\n".encode('utf-8'))
                comando = f"G1 E{unidades} F2000\n"
            elif eje_id == "E":
                self.serial_port.write("T1\n".encode('utf-8'))
                comando = f"G1 E{unidades} F2000\n"
            else:
                comando = f"G1 {eje_id}{unidades} F2000\n"
            
            self.serial_port.write(comando.encode('utf-8'))
            print(f"Enviado ({eje_id}): {comando.strip()}")
            
        except ValueError:
            print(f"Error: El valor ingresado para {eje_id} no es un número válido.")

    def fijar_cero_y_limites(self):
        """Desactiva límites de software y fija la posición actual como 0"""
        if self.serial_port and self.serial_port.is_open:
            # 1. Desactivar límites de software
            self.serial_port.write("M211 S0\n".encode('utf-8'))
            # 2. Establecer la posición actual como cero para X, Y, Z y Extrusores
            self.serial_port.write("G92 X0 Y0 Z0 E0\n".encode('utf-8'))
            print("Límites desactivados (M211 S0) y Posición fijada a Cero (G92).")
        else:
            print("Error: Puerto serial no conectado.")

    def cambiar_velocidad(self):
        """Cambia la velocidad global en tiempo real usando el Slider"""
        valor = self.slider_velocidad.value()
        self.lbl_velocidad_val.setText(f"{valor}%")
        if self.serial_port and self.serial_port.is_open:
            comando = f"M220 S{valor}\n"
            self.serial_port.write(comando.encode('utf-8'))
            print(f"Velocidad global ajustada: {comando.strip()}")

    def detener_servo(self):
        if self.serial_port and self.serial_port.is_open:
            comando = "M280 P0 S-1\n"
            self.serial_port.write(comando.encode('utf-8'))
            print("Enviado: Parada de Servo (S-1)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = BrazoRoboticoGUI()
    ventana.show()
    sys.exit(app.exec())