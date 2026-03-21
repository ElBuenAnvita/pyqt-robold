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
        self.setFixedSize(450, 400) # Ventana un poco más grande
        self.serial_port = None
        
        # Diccionario para guardar las referencias a las cajas de texto de cada motor
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
        # Formato: ('Nombre a mostrar', 'ID interno', 'Valor por defecto')
        ejes = [
            ("Base (X)", "X", "90"),
            ("Hombro (Y)", "Y", "90"),
            ("Codo (Z)", "Z", "90"),
            ("Muñeca 1 (T)", "T", "90"),
            ("Muñeca 2 (E)", "E", "90"),
            ("Garra (Servo)", "Servo", "180") # 180 suele ser abierto o cerrado según su ensamble
        ]
        
        for nombre, eje_id, val_defecto in ejes:
            layout_principal.addLayout(self.crear_fila_motor(nombre, eje_id, val_defecto))
        
        # 3. Botón de Parada de Emergencia / Detener Servo
        self.btn_stop = QPushButton("¡Detener Servo (S-1)!")
        self.btn_stop.setStyleSheet("background-color: #ff4c4c; color: white; font-weight: bold; padding: 5px;")
        self.btn_stop.clicked.connect(self.detener_servo)
        layout_principal.addWidget(self.btn_stop)

        # Ensamblar todo en la ventana
        widget_central = QWidget()
        widget_central.setLayout(layout_principal)
        self.setCentralWidget(widget_central)

    # --- FUNCIONES DE CREACIÓN DE UI ---
    def crear_fila_motor(self, nombre, eje_id, val_defecto):
        """Crea una fila con el Label, Input y Botón para un eje específico"""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"Motor {nombre}:"))
        
        input_val = QLineEdit(val_defecto)
        self.inputs[eje_id] = input_val # Guardamos el input en el diccionario usando su ID
        
        btn_mover = QPushButton(f"Mover {eje_id}")
        # La función lambda nos permite pasarle el eje_id a la función genérica cuando se hace clic
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
        """Función genérica que enruta el comando dependiendo del motor"""
        if not (self.serial_port and self.serial_port.is_open):
            print("Error: Puerto serial no conectado.")
            return
        
        try:
            valor = float(self.inputs[eje_id].text())
            
            # Caso especial 1: La Garra (Servomotor)
            if eje_id == "Servo":
                comando = f"M280 P0 S{valor}\n"
                self.serial_port.write(comando.encode('utf-8'))
                print(f"Enviado a Garra: {comando.strip()}")
                return

            # Para los motores paso a paso (X, Y, Z, T, E)
            unidades = valor / 2
            self.serial_port.write("G91\n".encode('utf-8')) # Movimiento relativo
            
            # Caso especial 2: Motores de los extrusores
            if eje_id == "T":
                self.serial_port.write("T0\n".encode('utf-8'))
                comando = f"G1 E{unidades} F2000\n"
            elif eje_id == "E":
                self.serial_port.write("T1\n".encode('utf-8'))
                comando = f"G1 E{unidades} F2000\n"
            # Caso normal: X, Y, Z
            else:
                comando = f"G1 {eje_id}{unidades} F2000\n"
            
            self.serial_port.write(comando.encode('utf-8'))
            print(f"Enviado ({eje_id}): {comando.strip()}")
            
        except ValueError:
            print(f"Error: El valor ingresado para {eje_id} no es un número válido.")

    def detener_servo(self):
        """Comando para cortar energía al servomotor"""
        if self.serial_port and self.serial_port.is_open:
            comando = "M280 P0 S-1\n"
            self.serial_port.write(comando.encode('utf-8'))
            print("Enviado: Parada de Servo (S-1)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = BrazoRoboticoGUI()
    ventana.show()
    sys.exit(app.exec())