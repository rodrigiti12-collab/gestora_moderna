
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
import os, json, datetime

DEFAULT_DATA = {"gastos": [], "ingresos": [], "deudores": [], "metas": [], "analisis_perm": False}

class SplashScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.manager.current.__setattr__('__ignored', None) or setattr(self.manager, 'current', 'menu'), 2)

class MenuScreen(Screen):
    tip = StringProperty("")
    total = NumericProperty(0.0)

class CalendarioScreen(Screen):
    pass

class GastosScreen(Screen):
    pass

class IngresosScreen(Screen):
    pass

class DeudoresScreen(Screen):
    pass

class MetasScreen(Screen):
    pass

class AnalisisScreen(Screen):
    resultado = StringProperty("")
    permiso_texto = StringProperty("")

class GestorApp(App):
    def build(self):
        self.title = "Gestora"
        kv = Builder.load_file("gestor.kv")
        self.data_file = os.path.join(self.user_data_dir, "database.json")
        self.datos = self._cargar_datos()
        self._actualizar_totales_y_tips(kv)
        return kv

    # ----------------- Persistencia -----------------
    def _cargar_datos(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w") as f:
                json.dump(DEFAULT_DATA, f, indent=2)
            return json.loads(json.dumps(DEFAULT_DATA))
        with open(self.data_file, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return json.loads(json.dumps(DEFAULT_DATA))

    def _guardar(self):
        with open(self.data_file, "w") as f:
            json.dump(self.datos, f, indent=2)

    # ----------------- Utilidades -----------------
    def _hoy(self):
        return datetime.date.today().isoformat()

    def _actualizar_totales_y_tips(self, root):
        total = sum(i.get("monto", 0) for i in self.datos["ingresos"]) - sum(g.get("monto", 0) for g in self.datos["gastos"])
        menu = root.get_screen("menu")
        menu.total = float(total)
        menu.tip = self._tip_del_dia()
        # Actualizar resúmenes simples
        self._refrescar_resumenes(root)

        # Analisis permiso texto
        analisis = root.get_screen("analisis")
        analisis.permiso_texto = "ON" if self.datos.get("analisis_perm") else "OFF"

    def _refrescar_resumenes(self, root):
        # Gastos
        gastos_txt = "\n".join([f"{g.get('fecha','')} - {g.get('categoria','?')}: ${g.get('monto',0):.2f} | {g.get('nota','')}" for g in self.datos["gastos"]][-100:])
        root.ids.gastos_resumen.text = gastos_txt if gastos_txt else "Sin gastos aún."
        # Ingresos
        ing_txt = "\n".join([f"{i.get('fecha','')} - {i.get('fuente','?')}: ${i.get('monto',0):.2f} | {i.get('nota','')}" for i in self.datos["ingresos"]][-100:])
        root.ids.ingresos_resumen.text = ing_txt if ing_txt else "Sin ingresos aún."
        # Deudores
        deu_txt = "\n".join([f"{d.get('nombre','?')} debe ${d.get('monto',0):.2f} | paga: {d.get('fecha_pago','?')} | excusa: {d.get('excusa','')}" for d in self.datos["deudores"]][-100:])
        root.ids.deudores_resumen.text = deu_txt if deu_txt else "Sin deudores."
        # Metas
        metas_txt = "\n".join([f"{m.get('titulo','?')} → objetivo: ${m.get('objetivo',0):.2f}" for m in self.datos["metas"]][-100:])
        root.ids.metas_resumen.text = metas_txt if metas_txt else "Sin metas aún."

        # Total en menú
        menu = root.get_screen("menu")
        menu.total = sum(i.get("monto", 0) for i in self.datos["ingresos"]) - sum(g.get("monto", 0) for g in self.datos["gastos"])

    def _tip_del_dia(self):
        tips = [
            "Tip: Registra primero tus ingresos fijos del mes.",
            "Tip: Un café al día suma más de lo que parece ☕",
            "Tip: Define un % para ahorro automático.",
            "Tip: Paga tus deudas más chicas primero.",
            "Tip: Revisa tus suscripciones mensuales."
        ]
        idx = datetime.date.today().toordinal() % len(tips)
        return tips[idx]

    # ----------------- Acciones desde la UI -----------------
    def add_gasto(self, monto, categoria, nota, fecha=""):
        try:
            monto = float(monto)
        except Exception:
            return
        if not fecha:
            fecha = self._hoy()
        self.datos["gastos"].append({"monto": monto, "categoria": categoria or "General", "nota": nota or "", "fecha": fecha})
        self._guardar()
        self._actualizar_totales_y_tips(self.root)

    def add_ingreso(self, monto, fuente, nota, fecha=""):
        try:
            monto = float(monto)
        except Exception:
            return
        if not fecha:
            fecha = self._hoy()
        self.datos["ingresos"].append({"monto": monto, "fuente": fuente or "Ingreso", "nota": nota or "", "fecha": fecha})
        self._guardar()
        self._actualizar_totales_y_tips(self.root)

    def add_deudor(self, nombre, monto, fecha_pago, excusa):
        try:
            monto = float(monto)
        except Exception:
            return
        self.datos["deudores"].append({"nombre": nombre or "Sin nombre", "monto": monto, "fecha_pago": fecha_pago or "?", "excusa": excusa or ""})
        self._guardar()
        self._actualizar_totales_y_tips(self.root)

    def add_meta(self, titulo, objetivo):
        try:
            objetivo = float(objetivo)
        except Exception:
            return
        self.datos["metas"].append({"titulo": titulo or "Meta", "objetivo": objetivo})
        self._guardar()
        self._actualizar_totales_y_tips(self.root)

    def toggle_analisis(self):
        self.datos["analisis_perm"] = not self.datos.get("analisis_perm", False)
        self._guardar()
        self.root.get_screen("analisis").permiso_texto = "ON" if self.datos["analisis_perm"] else "OFF"

    def analizar_dia(self, fecha=""):
        if not self.datos.get("analisis_perm"):
            self.root.get_screen("analisis").resultado = "Permiso desactivado."
            return
        if not fecha:
            fecha = self._hoy()
        # Agrupar gastos por categoría en la fecha
        totales = {}
        for g in self.datos["gastos"]:
            if g.get("fecha") == fecha:
                cat = g.get("categoria","General")
                totales[cat] = totales.get(cat, 0) + float(g.get("monto",0))
        if not totales:
            res = f"Sin gastos registrados el {fecha}."
        else:
            cat_top = max(totales, key=totales.get)
            monto_top = totales[cat_top]
            res = f"El {fecha}, gastaste más en '{cat_top}': ${monto_top:.2f}. Sugerencia: fija un tope o busca alternativas."
        self.root.get_screen("analisis").resultado = res

if __name__ == "__main__":
    GestorApp().run()
