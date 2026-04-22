from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QLineEdit, QSlider, QTextEdit
)
from PyQt6.QtCore import Qt


class InterfazBrazoUI(QWidget):
    def __init__(self):
        super().__init__()
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
            ("Muñeca 2 (Z)", "Z", "90")
        ]
        for nombre, eje_id, val_defecto in ejes:
            layout_principal.addLayout(self.crear_fila_motor(nombre, eje_id, val_defecto))

        # 3. Control Garra
        layout_principal.addWidget(QLabel("-----------------------------------------------------"))
        layout_principal.addWidget(QLabel("Control Garra (Servo Continuo):"))

        layout_vel_garra = QHBoxLayout()
        layout_vel_garra.addWidget(QLabel("Velocidad de Cierre/Apertura:"))
        self.slider_vel_garra = QSlider(Qt.Orientation.Horizontal)
        self.slider_vel_garra.setRange(10, 100)
        self.slider_vel_garra.setValue(100)
        self.lbl_vel_garra_val = QLabel("100%")

        layout_vel_garra.addWidget(self.slider_vel_garra)
        layout_vel_garra.addWidget(self.lbl_vel_garra_val)
        layout_principal.addLayout(layout_vel_garra)

        layout_botones_garra = QHBoxLayout()
        self.btn_abrir_garra = QPushButton("Abrir Garra")
        self.btn_abrir_garra.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.btn_cerrar_garra = QPushButton("Cerrar Garra")
        self.btn_cerrar_garra.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

        layout_botones_garra.addWidget(self.btn_abrir_garra)
        layout_botones_garra.addWidget(self.btn_cerrar_garra)
        layout_principal.addLayout(layout_botones_garra)

        layout_principal.addWidget(QLabel("-----------------------------------------------------"))

        # 4. Velocidad global
        layout_velocidad = QHBoxLayout()
        layout_velocidad.addWidget(QLabel("Velocidad Movimientos:"))
        self.slider_velocidad = QSlider(Qt.Orientation.Horizontal)
        self.slider_velocidad.setRange(10, 100)
        self.slider_velocidad.setValue(100)
        self.lbl_velocidad_val = QLabel("100%")
        self.btn_leer_pos = QPushButton("Consultar Posición")

        layout_velocidad.addWidget(self.slider_velocidad)
        layout_velocidad.addWidget(self.lbl_velocidad_val)
        layout_velocidad.addWidget(self.btn_leer_pos)
        layout_principal.addLayout(layout_velocidad)

        # 5. Botones del Sistema
        layout_sistema_1 = QHBoxLayout()
        self.btn_fijar_cero = QPushButton("Fijar Cero (Quitar Límites)")
        self.btn_fijar_cero.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;"
        )

        self.btn_stop = QPushButton("¡Detener Servo (S-1)!")
        self.btn_stop.setStyleSheet(
            "background-color: #ff4c4c; color: white; font-weight: bold; padding: 5px;"
        )

        layout_sistema_1.addWidget(self.btn_fijar_cero)
        layout_sistema_1.addWidget(self.btn_stop)
        layout_principal.addLayout(layout_sistema_1)

        layout_sistema_2 = QHBoxLayout()
        self.btn_centro_izq = QPushButton("Centro → Izquierda")
        self.btn_centro_izq.setStyleSheet(
            "background-color: #9C27B0; color: white; font-weight: bold; padding: 5px;"
        )

        self.btn_base_izq = QPushButton("Base → Izquierda")
        self.btn_base_izq.setStyleSheet(
            "background-color: #607D8B; color: white; font-weight: bold; padding: 5px;"
        )

        layout_sistema_2.addWidget(self.btn_centro_izq)
        layout_sistema_2.addWidget(self.btn_base_izq)
        layout_principal.addLayout(layout_sistema_2)

        # 6. Grabación / reproducción de movimientos
        layout_macro_1 = QHBoxLayout()
        self.btn_regresar_manual = QPushButton("Regresar Mov. Manuales")
        self.btn_regresar_manual.setStyleSheet(
            "background-color: #795548; color: white; font-weight: bold; padding: 5px;"
        )

        self.btn_quemar_rutina = QPushButton("Quemar Rutina")
        self.btn_quemar_rutina.setStyleSheet(
            "background-color: #3F51B5; color: white; font-weight: bold; padding: 5px;"
        )

        layout_macro_1.addWidget(self.btn_regresar_manual)
        layout_macro_1.addWidget(self.btn_quemar_rutina)
        layout_principal.addLayout(layout_macro_1)

        layout_macro_2 = QHBoxLayout()
        self.btn_ejecutar_rutina = QPushButton("Ejecutar Rutina Quemada")
        self.btn_ejecutar_rutina.setStyleSheet(
            "background-color: #009688; color: white; font-weight: bold; padding: 5px;"
        )

        self.btn_limpiar_rutina = QPushButton("Limpiar Rutina")
        self.btn_limpiar_rutina.setStyleSheet(
            "background-color: #9E9E9E; color: white; font-weight: bold; padding: 5px;"
        )

        layout_macro_2.addWidget(self.btn_ejecutar_rutina)
        layout_macro_2.addWidget(self.btn_limpiar_rutina)
        layout_principal.addLayout(layout_macro_2)

        # 7. Registro
        layout_principal.addWidget(QLabel("Registro de movimientos:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Aquí aparecerá el historial de movimientos y eventos...")
        self.txt_log.setMinimumHeight(180)
        layout_principal.addWidget(self.txt_log)

        self.setLayout(layout_principal)

    def crear_fila_motor(self, nombre, eje_id, val_defecto):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"Motor {nombre}:"))

        input_val = QLineEdit(val_defecto)
        input_val.setFixedWidth(50)
        self.inputs[eje_id] = input_val

        btn_mover = QPushButton(f"Mover {eje_id}")
        self.botones_mover[eje_id] = btn_mover

        lbl_pos = QLabel("Pos: 0.0°")
        lbl_pos.setStyleSheet("color: blue; font-weight: bold;")
        lbl_pos.setFixedWidth(80)
        self.labels_posicion[eje_id] = lbl_pos

        layout.addWidget(input_val)
        layout.addWidget(btn_mover)
        layout.addWidget(lbl_pos)
        return layout
