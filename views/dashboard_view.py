from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QGridLayout, QMessageBox,
                             QFrame, QScrollArea)
from PySide6.QtCore import Qt, QTimer
from utils.signals import signal_manager
from PySide6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis, QPieSeries, QPieSlice
from PySide6.QtGui import QPainter, QLinearGradient, QGradient, QColor
import qtawesome as qta
from datetime import datetime
from utils.translation_manager import tr, tr_manager

class DashboardView(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.setup_ui()

        # Auto-refresh every 30 seconds
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(30000)

        # Signal-based instant refresh
        signal_manager.item_changed.connect(self.refresh)
        signal_manager.movement_added.connect(self.refresh)
        signal_manager.supplier_changed.connect(self.refresh)

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for high-density data
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        layout = QVBoxLayout(self.scroll_content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(35)
        scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(scroll)

        # Header with Logo/Title
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #111; border-bottom: 2px solid #d4af37; padding: 15px;")
        header_h = QHBoxLayout(header_frame)

        logo_icon = QLabel()
        import os
        if os.path.exists("logo/logo.png"):
            from PySide6.QtGui import QPixmap
            logo_pix = QPixmap("logo/logo.png").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_icon.setPixmap(logo_pix)
        else:
            logo_icon.setPixmap(qta.icon("fa5s.shield-alt", color="#d4af37").pixmap(45, 45))
        header_h.addWidget(logo_icon)

        header_title = QLabel("AMERICAN MARINE SERVICES FREEZONE")
        header_title.setStyleSheet("font-size: 30px; font-weight: 900; color: #d4af37; letter-spacing: 3px; font-family: 'Georgia';")
        header_h.addWidget(header_title)

        header_h.addStretch()

        control_label = QLabel(tr("system_subtitle").upper())
        control_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #7f8c8d; border: 1px solid #333; padding: 5px 15px; border-radius: 15px;")
        header_h.addWidget(control_label)

        self.last_updated_label = QLabel("Last Updated: --:--:--")
        self.last_updated_label.setStyleSheet("color: #555; font-size: 10px; margin-right: 20px;")
        header_h.addWidget(self.last_updated_label)

        layout.addWidget(header_frame)

        # Top Stats Cards
        stats_h_layout = QHBoxLayout()
        stats_h_layout.setSpacing(20)

        self.total_items_card = self.create_stat_card(tr("total_items"), "0", "fa5s.boxes", "#1a2a6c")
        self.total_in_card = self.create_stat_card(tr("stock_in"), "0", "fa5s.download", "#27ae60")
        self.total_out_card = self.create_stat_card(tr("stock_out"), "0", "fa5s.upload", "#e67e22")
        self.profit_card = self.create_stat_card("Est. Profit", "0", "fa5s.chart-line", "#f1c40f")
        self.total_value_card = self.create_stat_card(tr("total_value"), "0.00", "fa5s.money-bill-wave", "#2ecc71")
        self.expiring_card = self.create_stat_card(tr("expiring_soon"), "0", "fa5s.calendar-times", "#e74c3c")

        stats_h_layout.addWidget(self.total_items_card)
        stats_h_layout.addWidget(self.total_in_card)
        stats_h_layout.addWidget(self.total_out_card)
        stats_h_layout.addWidget(self.profit_card)
        stats_h_layout.addWidget(self.total_value_card)
        stats_h_layout.addWidget(self.expiring_card)
        layout.addLayout(stats_h_layout)

        # Middle Section (Charts)
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(30)

        # Bar Chart for 7-day trend
        self.activity_chart = QChart()
        self.activity_chart.setTitle(tr("activity_7d"))
        self.activity_chart.setAnimationOptions(QChart.SeriesAnimations)

        self.chart_view = QChartView(self.activity_chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(350)
        charts_layout.addWidget(self.chart_view, 2)

        # Pie Chart for Categories
        self.pie_chart = QChart()
        self.pie_chart.setTitle(tr("category_distribution"))
        self.pie_chart_view = QChartView(self.pie_chart)
        self.pie_chart_view.setRenderHint(QPainter.Antialiasing)
        self.pie_chart_view.setMinimumHeight(350)
        charts_layout.addWidget(self.pie_chart_view, 1)

        layout.addLayout(charts_layout)

        # Middle-Bottom Section: Smart Critical Lists (Level 9)
        critical_layout = QHBoxLayout()
        critical_layout.setSpacing(30)

        # Low Stock List
        ls_frame = QFrame()
        ls_frame.setStyleSheet("background-color: #1c1e26; border-radius: 15px; padding: 15px;")
        ls_vbox = QVBoxLayout(ls_frame)

        ls_h = QHBoxLayout()
        ls_header = QLabel(tr("low_stock_details").upper())
        ls_header.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")
        ls_h.addWidget(ls_header)

        self.view_ls_btn = QPushButton(tr("view_analysis"))
        self.view_ls_btn.setStyleSheet("color: #d4af37; font-size: 10px; border: none; text-decoration: underline;")
        self.view_ls_btn.setVisible(False)
        ls_h.addWidget(self.view_ls_btn, 0, Qt.AlignRight)
        ls_vbox.addLayout(ls_h)

        self.ls_list = QVBoxLayout()
        ls_vbox.addLayout(self.ls_list)
        ls_vbox.addStretch()
        critical_layout.addWidget(ls_frame, 1)

        # Expiring Soon List
        ex_frame = QFrame()
        ex_frame.setStyleSheet("background-color: #1c1e26; border-radius: 15px; padding: 15px;")
        ex_vbox = QVBoxLayout(ex_frame)

        ex_h = QHBoxLayout()
        ex_header = QLabel(tr("expiring_details").upper())
        ex_header.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 14px;")
        ex_h.addWidget(ex_header)

        self.view_ex_btn = QPushButton(tr("view_analysis"))
        self.view_ex_btn.setStyleSheet("color: #d4af37; font-size: 10px; border: none; text-decoration: underline;")
        self.view_ex_btn.setVisible(False)
        ex_h.addWidget(self.view_ex_btn, 0, Qt.AlignRight)
        ex_vbox.addLayout(ex_h)

        self.ex_list = QVBoxLayout()
        ex_vbox.addLayout(self.ex_list)
        ex_vbox.addStretch()
        critical_layout.addWidget(ex_frame, 1)

        layout.addLayout(critical_layout)

        # Bottom Section: High-Density Analytics
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(30)

        # Performance Spotlight (New Location)
        performance_frame = QFrame()
        performance_frame.setStyleSheet("background-color: #1c1e26; border-radius: 15px; padding: 20px;")
        perf_vbox = QVBoxLayout(performance_frame)
        perf_header = QLabel(tr("top_performance"))
        perf_header.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 14px;")
        perf_vbox.addWidget(perf_header)

        self.top_supplier_label = QLabel("N/A")
        self.top_supplier_label.setStyleSheet("color: #ecf0f1; font-size: 15px; font-weight: bold;")
        perf_vbox.addWidget(QLabel(tr("top_supplier") + ":"))
        perf_vbox.addWidget(self.top_supplier_label)

        perf_vbox.addStretch()
        bottom_layout.addWidget(performance_frame, 1)

        # Alerts
        alerts_frame = QFrame()
        alerts_frame.setStyleSheet("background-color: #1c1e26; border-radius: 15px; padding: 20px;")
        alerts_vbox = QVBoxLayout(alerts_frame)
        alerts_header = QLabel(tr("smart_alerts"))
        alerts_header.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 14px;")
        alerts_vbox.addWidget(alerts_header)

        self.alerts_label = QLabel(tr("system_status_ok"))
        self.alerts_label.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: bold;")
        self.alerts_label.setWordWrap(True)
        alerts_vbox.addWidget(self.alerts_label)
        alerts_vbox.addStretch()
        bottom_layout.addWidget(alerts_frame, 1)

        # Top Moving Items
        top_items_frame = QFrame()
        top_items_frame.setStyleSheet("background-color: #1c1e26; border-radius: 15px; padding: 20px;")
        top_vbox = QVBoxLayout(top_items_frame)
        top_header = QLabel(tr("top_moving_items"))
        top_header.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 14px;")
        top_vbox.addWidget(top_header)

        self.top_items_list = QVBoxLayout()
        top_vbox.addLayout(self.top_items_list)
        top_vbox.addStretch()
        bottom_layout.addWidget(top_items_frame, 1)

        # Live Feed (Level 9)
        live_frame = QFrame()
        live_frame.setStyleSheet("background-color: #1c1e26; border-radius: 15px; padding: 20px;")
        live_vbox = QVBoxLayout(live_frame)

        live_h = QHBoxLayout()
        live_header = QLabel(tr("live_movement_feed"))
        live_header.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 14px;")
        live_h.addWidget(live_header)

        view_all_btn = QPushButton(tr("view_analysis"))
        view_all_btn.setStyleSheet("color: #d4af37; font-size: 11px; border: none; text-decoration: underline;")
        live_h.addWidget(view_all_btn, 0, Qt.AlignRight)
        live_vbox.addLayout(live_h)

        self.live_feed_list = QVBoxLayout()
        live_vbox.addLayout(self.live_feed_list)
        live_vbox.addStretch()
        bottom_layout.addWidget(live_frame, 1.5)

        layout.addLayout(bottom_layout)

        layout.addStretch()
        self.refresh()

    def create_stat_card(self, title, value, icon, color):
        card = QFrame()
        card.setObjectName("ProStatCard")
        card.setMinimumHeight(140)
        card.setStyleSheet(f"""
            QFrame#ProStatCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1c1e26, stop:1 #2c3e50);
                border-bottom: 3px solid {color};
                border-radius: 15px;
                padding: 18px;
            }}
            QFrame#ProStatCard:hover {{
                border-bottom: 5px solid {color};
                background: #242730;
            }}
        """)

        card_layout = QHBoxLayout(card)

        text_layout = QVBoxLayout()
        title_label = QLabel(title.upper())
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #95a5a6;")

        val_label = QLabel(value)
        val_label.setStyleSheet(f"font-size: 36px; font-weight: 900; color: #ecf0f1;")
        val_label.setObjectName("ValueLabel")

        text_layout.addWidget(title_label)
        text_layout.addStretch()
        text_layout.addWidget(val_label)

        card_layout.addLayout(text_layout)
        card_layout.addStretch()

        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon, color=color).pixmap(55, 55))
        card_layout.addWidget(icon_label)

        return card

    def refresh(self):
        from workers.worker import Worker
        from PySide6.QtCore import QThreadPool
        worker = Worker(self.service.get_stats)
        worker.signals.result.connect(self.on_stats_loaded)
        QThreadPool.globalInstance().start(worker)

    def on_stats_loaded(self, stats):
        try:
            # Update Cards
            self.total_items_card.findChild(QLabel, "ValueLabel").setText(str(stats.get('total_items', 0)))
            self.total_in_card.findChild(QLabel, "ValueLabel").setText(f"{stats.get('total_in', 0):,.0f}")
            self.total_out_card.findChild(QLabel, "ValueLabel").setText(f"{stats.get('total_out', 0):,.0f}")
            self.profit_card.findChild(QLabel, "ValueLabel").setText(f"{stats.get('profit_est', 0):,.0f}")
            self.expiring_card.findChild(QLabel, "ValueLabel").setText(str(stats.get('expiring_soon', 0)))
            self.total_value_card.findChild(QLabel, "ValueLabel").setText(f"{stats.get('total_value', 0):,.2f}")

            # Update Bar Chart (Detailed Daily Trend)
            self.activity_chart.removeAllSeries()
            trends = stats.get('trends', [])
            set_in = QBarSet(tr("inbound"))
            set_out = QBarSet(tr("outbound"))

            categories = []
            for t in trends:
                set_in.append(t['in'])
                set_out.append(t['out'])
                categories.append(t['date'])

            series = QBarSeries()
            series.append(set_in)
            series.append(set_out)
            self.activity_chart.addSeries(series)

            # Re-create axes for the chart
            self.activity_chart.createDefaultAxes()
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            self.activity_chart.setAxisX(axis_x, series)

            # Update Pie Chart (Categories)
            self.pie_chart.removeAllSeries()
            pie_series = QPieSeries()
            cat_dist = stats.get('category_dist', {})
            for cat, count in cat_dist.items():
                slice = pie_series.append(f"{cat}", count)
                slice.setLabelVisible(True)

            if pie_series.count() > 0:
                self.pie_chart.addSeries(pie_series)

            # Update Alerts
            alert_text = []
            if stats.get('low_stock', 0) > 0:
                alert_text.append(f"⚠️ {tr('low_stock_alert')}: {stats['low_stock']}")
            if stats.get('expiring_soon', 0) > 0:
                alert_text.append(f"⏰ {tr('expiring_soon_alert')}: {stats['expiring_soon']}")

            if alert_text:
                self.alerts_label.setText("\n".join(alert_text))
                self.alerts_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px;")
                # Push Toast Notification
                from utils.notifications import NotificationManager
                NotificationManager.warning(self.window(), tr("smart_alerts"), "\n".join(alert_text))
            else:
                self.alerts_label.setText(tr("system_status_ok"))
                self.alerts_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 16px;")

            # Update Top Items
            while self.top_items_list.count():
                child = self.top_items_list.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            for item in stats.get('top_moving', []):
                unit_txt = tr("unit") if tr_manager.current_language == 'ar' else "units"
                item_row = QLabel(f"• {item['name']} ({int(item['value'])} {unit_txt})")
                item_row.setStyleSheet("color: #ecf0f1; font-size: 13px; padding: 2px;")
                self.top_items_list.addWidget(item_row)

            # Update Live Feed
            while self.live_feed_list.count():
                child = self.live_feed_list.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            for m in stats.get('live_feed', [])[:7]: # Limit to 7 items
                color = "#27ae60" if m['type'] == 'IN' else "#e74c3c"
                m_type_txt = tr("inbound") if m['type'] == 'IN' else tr("outbound")
                feed_row = QLabel(f"[{m['time']}] {m_type_txt}: {m['ref']} ({int(m['qty'])} items)")
                feed_row.setStyleSheet(f"color: {color}; font-size: 12px; font-family: 'Consolas';")
                self.live_feed_list.addWidget(feed_row)

            # Update Low Stock Details
            while self.ls_list.count():
                child = self.ls_list.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            ls_data = stats.get('low_stock_details', [])
            self.view_ls_btn.setVisible(len(ls_data) > 7)
            for i in ls_data[:7]:
                row = QLabel(f"• {i['name']} ({i['stock']}) | {i['supplier']} | ${i['last_price']:,.2f}")
                row.setStyleSheet("color: #ecf0f1; font-size: 12px; padding: 2px;")
                self.ls_list.addWidget(row)

            # Update Expiring Details
            while self.ex_list.count():
                child = self.ex_list.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            ex_data = stats.get('expiring_details', [])
            self.view_ex_btn.setVisible(len(ex_data) > 7)
            for e in ex_data[:7]:
                row = QLabel(f"• {e['name']} (Lot: {e['lot']}) | Exp: {e['expiry']} | Qty: {e['qty']}")
                row.setStyleSheet("color: #ecf0f1; font-size: 12px; padding: 2px;")
                self.ex_list.addWidget(row)

            # Update Performance Spotlight
            top_s = stats.get('top_supplier', {})
            self.top_supplier_label.setText(f"{top_s.get('name', 'N/A')} ({top_s.get('value', 0):,.2f})")

            self.last_updated_label.setText(f"Last Synced: {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            from app_logging.app_logger import app_logger
            app_logger.error(f"Dashboard refresh error: {e}")
