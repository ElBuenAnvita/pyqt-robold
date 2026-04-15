from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QComboBox, QLabel, QLineEdit, QSlider)
from PyQt6.QtCore import Qt

class InterfazBrazoUI(QWidget):
    def __init__(self):
        super().__init__()
        # Diccionarios para almacenar referencias a los elementos visuales
        self.inputs = {}
        self.botones_mover = {}
        self.labels_posicion = {}
        
        self.construir_ui()

    def construir_ui(self):
        layout_principal = QVBoxLayout()
        
        # 1. Panel de Conexión
        layout_conexion = QHBoxLayout()
        self.combo_puertos = QComboBox()
        self.btn_conectar = QPushButton("Conectar")
        self.lbl_estado = QLabel("Desconectado")
        self.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
        
        layout_conexion.addWidget(self.combo_puertos)
        layout_conexion.addWidget(self.btn_conectar)
        layout_conexion.addWidget(self.lbl_estado)
        layout_principal.addLayout(layout_conexion)
        
        # 2. Filas de Motores
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
            
        # 3. Slider de Velocidad
        layout_velocidad = QHBoxLayout()
        layout_velocidad.addWidget(QLabel("Velocidad Global:"))
        
        self.slider_velocidad = QSlider(Qt.Orientation.Horizontal)
        self.slider_velocidad.setRange(10, 100) 
        self.slider_velocidad.setValue(100) 
        
        self.lbl_velocidad_val = QLabel("100%")
        self.btn_leer_pos = QPushButton("Consultar Posición (M114)")
        self.btn_leer_pos.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        
        layout_velocidad.addWidget(self.slider_velocidad)
        layout_velocidad.addWidget(self.lbl_velocidad_val)
        layout_velocidad.addWidget(self.btn_leer_pos)
        layout_principal.addLayout(layout_velocidad)
        
        # 4. Botones del Sistema
        layout_sistema = QHBoxLayout()
        self.btn_fijar_cero = QPushButton("Fijar Cero (Quitar Límites)")
        self.btn_fijar_cero.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        
        self.btn_stop = QPushButton("¡Detener Servo (S-1)!")
        self.btn_stop.setStyleSheet("background-color: #ff4c4c; color: white; font-weight: bold; padding: 5px;")
        
        layout_sistema.addWidget(self.btn_fijar_cero)
        layout_sistema.addWidget(self.btn_stop)
        layout_principal.addLayout(layout_sistema)

        self.setLayout(layout_principal)

    def crear_fila_motor(self, nombre, eje_id, val_defecto):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"Motor {nombre}:"))
        
        input_val = QLineEdit(val_defecto)
        input_val.setFixedWidth(50)
        self.inputs[eje_id] = input_val 
        
        btn_mover = QPushButton(f"Mover {eje_id}")
        self.botones_mover[eje_id] = btn_mover # Guardamos referencia del botón
        
        lbl_pos = QLabel("Pos: 0.0°")
        lbl_pos.setStyleSheet("color: blue; font-weight: bold;")
        lbl_pos.setFixedWidth(80)
        self.labels_posicion[eje_id] = lbl_pos
        
        layout.addWidget(input_val)
        layout.addWidget(btn_mover)
        layout.addWidget(lbl_pos)
        return layout