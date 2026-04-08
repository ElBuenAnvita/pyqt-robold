import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QSlider)
from PyQt6.QtCore import Qt, QTimer

class BrazoRoboticoGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Brazo 6DOF - TinyBee")
        self.setFixedSize(550, 480) # Ventana un poco más ancha para mostrar la posición
        self.serial_port = None
        
        self.inputs = {}
        self.labels_posicion = {} # Diccionario para guardar los labels que muestran la posición
        
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
            
        # 3. Control de Velocidad (Slider) y Botón de Leer Posición
        layout_velocidad = QHBoxLayout()
        layout_velocidad.addWidget(QLabel("Velocidad Global:"))
        
        self.slider_velocidad = QSlider(Qt.Orientation.Horizontal)
        self.slider_velocidad.setRange(10, 100) 
        self.slider_velocidad.setValue(100) 
        self.slider_velocidad.valueChanged.connect(self.cambiar_velocidad)
        self.lbl_velocidad_val = QLabel("100%")
        
        self.btn_leer_pos = QPushButton("Consultar Posición (M114)")
        self.btn_leer_pos.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_leer_pos.clicked.connect(self.solicitar_posicion)
        
        layout_velocidad.addWidget(self.slider_velocidad)
        layout_velocidad.addWidget(self.lbl_velocidad_val)
        layout_velocidad.addWidget(self.btn_leer_pos)
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

        # --- TIMER PARA LEER SERIAL EN SEGUNDO PLANO ---
        self.timer_serial = QTimer()
        self.timer_serial.timeout.connect(self.leer_puerto_serial)

    # --- FUNCIONES DE CREACIÓN DE UI ---
    def crear_fila_motor(self, nombre, eje_id, val_defecto):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"Motor {nombre}:"))
        
        input_val = QLineEdit(val_defecto)
        input_val.setFixedWidth(50)
        self.inputs[eje_id] = input_val 
        
        btn_mover = QPushButton(f"Mover {eje_id}")
        btn_mover.clicked.connect(lambda checked, e=eje_id: self.mover_motor(e))
        
        # Nuevo Label para mostrar la posición que nos reporta Marlin
        lbl_pos = QLabel("Pos: 0.0°")
        lbl_pos.setStyleSheet("color: blue; font-weight: bold;")
        lbl_pos.setFixedWidth(80)
        self.labels_posicion[eje_id] = lbl_pos
        
        layout.addWidget(input_val)
        layout.addWidget(btn_mover)
        layout.addWidget(lbl_pos) # Lo añadimos al final de la fila
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
                self.serial_port = serial.Serial(puerto_seleccionado, 115200, timeout=0.1)
                self.lbl_estado.setText("Conectado")
                self.lbl_estado.setStyleSheet("color: green; font-weight: bold;")
                self.btn_conectar.setText("Desconectar")
                
                # Encendemos el reloj invisible para que lea el serial cada 100 milisegundos
                self.timer_serial.start(100) 
            except Exception as e:
                self.lbl_estado.setText(f"Error: {str(e)}")
        else:
            self.timer_serial.stop() # Apagamos el reloj
            self.serial_port.close()
            self.lbl_estado.setText("Desconectado")
            self.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
            self.btn_conectar.setText("Conectar")

    def mover_motor(self, eje_id):
        if not (self.serial_port and self.serial_port.is_open):
            return
        
        try:
            valor = float(self.inputs[eje_id].text())
            if eje_id == "Servo":
                self.serial_port.write(f"M280 P0 S{valor}\n".encode('utf-8'))
                return

            unidades = valor # / 2
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
            
            # Pedir a Marlin que nos confirme su nueva posición después de moverse
            self.solicitar_posicion()
            
        except ValueError:
            print("Error: Ingrese un número válido.")

    def solicitar_posicion(self):
        """Envía el comando M114 para pedirle a Marlin su ubicación actual"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write("M114\n".encode('utf-8'))

    def leer_puerto_serial(self):
        """Se ejecuta en segundo plano. Si Marlin envía texto, lo lee y lo procesa."""
        if self.serial_port and self.serial_port.is_open:
            if self.serial_port.in_waiting > 0:
                respuesta = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                
                # Filtro de limpieza: Ignoramos el spam de "wait" y los acuses de recibo "ok" simples
                if respuesta == "wait" or respuesta.startswith("ok"):
                    return
                    
                print(f"Marlin dice: {respuesta}")
                
                if "X:" in respuesta and "Count" in respuesta:
                    self.procesar_coordenadas(respuesta)

    def procesar_coordenadas(self, texto):
        """Extrae los números del texto de Marlin y los convierte a grados reales"""
        # texto llega así: "X:180.00 Y:0.00 Z:0.00 E:0.00 Count X:1598 Y:0 Z:0"
        # 1. Cortamos en la palabra " Count " y nos quedamos solo con la primera mitad [0]
        texto_limpio = texto.split(" Count ")[0] 
        
        # 2. Ahora sí separamos por espacios. Queda: ["X:180.00", "Y:0.00", "Z:0.00", "E:0.00"]
        partes = texto_limpio.split()
        
        for parte in partes:
            if parte.startswith("X:"):
                grados = float(parte.replace("X:", ""))# / 2 
                self.labels_posicion["X"].setText(f"Pos: {grados:.1f}°")
                
            elif parte.startswith("Y:"):
                grados = float(parte.replace("Y:", ""))#  / 2
                self.labels_posicion["Y"].setText(f"Pos: {grados:.1f}°")
                
            elif parte.startswith("Z:"):
                grados = float(parte.replace("Z:", ""))#  / 2
                self.labels_posicion["Z"].setText(f"Pos: {grados:.1f}°")
                
            elif parte.startswith("E:"):
                grados = float(parte.replace("E:", ""))#  / 2
                self.labels_posicion["T"].setText(f"Pos: {grados:.1f}°")

    def fijar_cero_y_limites(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write("M211 S0\n".encode('utf-8'))
            self.serial_port.write("G92 X0 Y0 Z0 E0\n".encode('utf-8'))
            self.solicitar_posicion() # Actualizar UI a cero

    def cambiar_velocidad(self):
        valor = self.slider_velocidad.value()
        self.lbl_velocidad_val.setText(f"{valor}%")
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(f"M220 S{valor}\n".encode('utf-8'))

    def detener_servo(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write("M280 P0 S-1\n".encode('utf-8'))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = BrazoRoboticoGUI()
    ventana.show()
    sys.exit(app.exec())