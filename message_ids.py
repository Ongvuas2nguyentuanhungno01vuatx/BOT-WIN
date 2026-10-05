# -*- coding: utf-8 -*-
# ============================================================
# BOT TELEGRAM DỰ ĐOÁN TÀI XỈU + SICBO + MD5 CHẴN LẺ
# Nguồn dữ liệu: @Ongvuas2nguyentuanhungno1
# Không cần .env — Config hardcode trực tiếp
# ============================================================

import re
import os
import json
import time
import hashlib
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ============================================================
# ⚙️ CẤU HÌNH — SỬA TRỰC TIẾP Ở ĐÂY
# ============================================================
BOT_TOKEN = "8539271780:AAGn88Crbrs9VVTfCsfRJ_J2GBc3Id-GBSA"
ADMIN_ID = 123456789
ADMIN_USERNAME = "@Ongvuas2nguyentuanhungno1"

# API endpoints — LATEST
API_TAIXIU = "https://kwinstore.com/sunwin/tx/a54a10c078b0bdbbccce0f732823ceefa4f3ea59c6cbe1ed"
API_SICBO = "https://kwinstore.com/sunwin/sicbo/a54a10c078b0bdbbccce0f732823ceefa4f3ea59c6cbe1ed"

# API endpoints — HISTORY
API_TAIXIU_HISTORY = "https://kwinstore.com/sunwin/tx/history/a54a10c078b0bdbbccce0f732823ceefa4f3ea59c6cbe1ed"
API_SICBO_HISTORY = "https://kwinstore.com/sunwin/sicbo/history/a54a10c078b0bdbbccce0f732823ceefa4f3ea59c6cbe1ed"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

HISTORY_FILE = "dudoan_history.json"

# ------------------------------------------------------------
# LỚP GỌI API
# ------------------------------------------------------------
class APIKwinstore:
    """Lớp gọi API Tài Xỉu và Sicbo."""

    @staticmethod
    def lay_tai_xiu():
        """Lấy kết quả Tài Xỉu mới nhất."""
        try:
            response = requests.get(API_TAIXIU, headers=HEADERS, timeout=15)
            data = response.json()
            if data.get("success"):
                return {
                    "ket_qua": data["data"].get("ket_qua", ""),
                    "phien": data["data"].get("phien", ""),
                    "thoi_gian": data["data"].get("thoi_gian", ""),
                    "tong": data["data"].get("tong", 0),
                    "xuc_xac": [
                        data["data"].get("xuc_xac_1", 0),
                        data["data"].get("xuc_xac_2", 0),
                        data["data"].get("xuc_xac_3", 0),
                    ]
                }
            return None
        except Exception as e:
            return {"loi": str(e)}

    @staticmethod
    def lay_sicbo():
        """Lấy kết quả Sicbo mới nhất."""
        try:
            response = requests.get(API_SICBO, headers=HEADERS, timeout=15)
            data = response.json()
            if data.get("success"):
                return {
                    "ket_qua": data["data"].get("ket_qua", ""),
                    "phien": data["data"].get("phien", ""),
                    "tong": data["data"].get("tong", 0),
                    "xuc_xac": [
                        data["data"].get("xuc_xac_1", 0),
                        data["data"].get("xuc_xac_2", 0),
                        data["data"].get("xuc_xac_3", 0),
                    ],
                    "keyR": data["data"].get("keyR", ""),
                }
            return None
        except Exception as e:
            return {"loi": str(e)}

    @staticmethod
    def lay_lich_su_tai_xiu(so_luong=20):
        """Lấy lịch sử Tài Xỉu."""
        try:
            response = requests.get(API_TAIXIU_HISTORY, headers=HEADERS, timeout=15)
            data = response.json()
            if data.get("status") == "OK" and isinstance(data.get("data"), list):
                ket_qua = []
                for item in data["data"][:so_luong]:
                    ket_qua.append({
                        "phien": item.get("phiên") or item.get("phien"),
                        "ket_qua": item.get("kết quả") or item.get("ket_qua", ""),
                        "tong": item.get("tổng") or item.get("tong"),
                        "d1": item.get("d1"),
                        "d2": item.get("d2"),
                        "d3": item.get("d3"),
                        "thoi_gian": item.get("updatedAt", "")
                    })
                return ket_qua
            return []
        except Exception as e:
            print(f"Lỗi lấy lịch sử TX: {e}")
            return []

    @staticmethod
    def lay_lich_su_sicbo(so_luong=20):
        """Lấy lịch sử Sicbo."""
        try:
            response = requests.get(API_SICBO_HISTORY, headers=HEADERS, timeout=15)
            data = response.json()
            if data.get("status") == "OK" and isinstance(data.get("data"), list):
                ket_qua = []
                for item in data["data"][:so_luong]:
                    ket_qua.append({
                        "phien": item.get("phiên") or item.get("phien"),
                        "ket_qua": item.get("kết quả") or item.get("ket_qua", ""),
                        "tong": item.get("tổng") or item.get("tong"),
                        "d1": item.get("d1"),
                        "d2": item.get("d2"),
                        "d3": item.get("d3"),
                        "thoi_gian": item.get("updatedAt", "")
                    })
                return ket_qua
            return []
        except Exception as e:
            print(f"Lỗi lấy lịch sử Sicbo: {e}")
            return []

# ------------------------------------------------------------
# THUẬT TOÁN DỰ ĐOÁN TÀI XỈU
# ------------------------------------------------------------
class ThuanToanDuDoan:
    def __init__(self):
        self.lich_su = []

    def nap_lich_su(self, danh_sach):
        self.lich_su = []
        for item in danh_sach:
            kq = item.get("ket_qua", "").lower()
            if "tài" in kq or "tai" in kq:
                self.lich_su.append("T")
            elif "xỉu" in kq or "xiu" in kq:
                self.lich_su.append("X")

    def phan_tich(self):
        if len(self.lich_su) < 3:
            return {"cau": "Chưa đủ dữ liệu", "do_tin_cay": 0}

        phan_tich = {}
        dem_bet = 1
        for i in range(1, len(self.lich_su)):
            if self.lich_su[i] == self.lich_su[i-1]:
                dem_bet += 1
            else:
                break
        phan_tich['cau_bet'] = dem_bet
        phan_tich['cau_bet_ket_qua'] = self.lich_su[0] if self.lich_su else None
        phan_tich['ty_le_tai'] = self.lich_su.count('T') / len(self.lich_su)
        phan_tich['ty_le_xiu'] = self.lich_su.count('X') / len(self.lich_su)
        if len(self.lich_su) >= 4:
            phan_tich['cau_1_1'] = all(self.lich_su[i] != self.lich_su[i+1] for i in range(min(4, len(self.lich_su)-1)))
        else:
            phan_tich['cau_1_1'] = False
        return phan_tich

    def du_doan(self):
        phan_tich = self.phan_tich()
        ly_do = []
        diem_tai = 50
        diem_xiu = 50

        if phan_tich.get('cau_bet', 0) >= 3:
            if phan_tich['cau_bet_ket_qua'] == 'T':
                diem_tai += 20
                ly_do.append(f"Cầu bệt Tài {phan_tich['cau_bet']} tay")
            else:
                diem_xiu += 20
                ly_do.append(f"Cầu bệt Xỉu {phan_tich['cau_bet']} tay")

        if phan_tich.get('cau_1_1'):
            if self.lich_su[0] == 'T':
                diem_xiu += 15
                ly_do.append("Cầu 1-1, ván trước Tài → nghiêng Xỉu")
            else:
                diem_tai += 15
                ly_do.append("Cầu 1-1, ván trước Xỉu → nghiêng Tài")

        if phan_tich.get('ty_le_tai', 0.5) > 0.6:
            diem_xiu += 10
            ly_do.append("Tỷ lệ Tài cao → có thể đảo Xỉu")
        elif phan_tich.get('ty_le_tai', 0.5) < 0.4:
            diem_tai += 10
            ly_do.append("Tỷ lệ Xỉu cao → có thể đảo Tài")

        if diem_tai > diem_xiu:
            return {'ket_qua': 'T', 'do_tin_cay': min(diem_tai, 100), 'ly_do': ly_do}
        elif diem_xiu > diem_tai:
            return {'ket_qua': 'X', 'do_tin_cay': min(diem_xiu, 100), 'ly_do': ly_do}
        else:
            if self.lich_su and self.lich_su[0] == 'T':
                return {'ket_qua': 'X', 'do_tin_cay': 55, 'ly_do': ly_do + ["Hòa điểm, đảo chiều"]}
            else:
                return {'ket_qua': 'T', 'do_tin_cay': 55, 'ly_do': ly_do + ["Hòa điểm, đảo chiều"]}

# ------------------------------------------------------------
# THUẬT TOÁN DỰ ĐOÁN MD5 CHẴN LẺ
# ------------------------------------------------------------
class ThuanToanMD5:
    def __init__(self, chuoi_md5):
        self.chuoi = chuoi_md5.lower()
        self.hop_le = bool(re.fullmatch(r'[a-f0-9]{32}', self.chuoi))

    def phan_tich(self):
        if not self.hop_le:
            return None
        so_nguyen = int(self.chuoi, 16)
        tong_hex = sum(int(c, 16) for c in self.chuoi)
        so_chan = sum(1 for c in self.chuoi if int(c, 16) % 2 == 0)
        so_le = 32 - so_chan
        ky_tu_dau = self.chuoi[0]
        ky_tu_cuoi = self.chuoi[-1]
        return {
            "so_nguyen": so_nguyen,
            "tong_hex": tong_hex,
            "so_chan": so_chan,
            "so_le": so_le,
            "ky_tu_dau": ky_tu_dau,
            "ky_tu_cuoi": ky_tu_cuoi
        }

    def du_doan(self):
        pt = self.phan_tich()
        if not pt:
            return None
        diem_chan = 50
        diem_le = 50
        ly_do = []

        if pt['tong_hex'] % 2 == 0:
            diem_chan += 10
            ly_do.append(f"Tổng hex = {pt['tong_hex']} (chẵn) → nghiêng Chẵn")
        else:
            diem_le += 10
            ly_do.append(f"Tổng hex = {pt['tong_hex']} (lẻ) → nghiêng Lẻ")

        if pt['so_chan'] > pt['so_le']:
            diem_chan += 15
            ly_do.append(f"{pt['so_chan']} ký tự chẵn > {pt['so_le']} ký tự lẻ → nghiêng Chẵn")
        elif pt['so_le'] > pt['so_chan']:
            diem_le += 15
            ly_do.append(f"{pt['so_le']} ký tự lẻ > {pt['so_chan']} ký tự chẵn → nghiêng Lẻ")

        if int(pt['ky_tu_cuoi'], 16) % 2 == 0:
            diem_chan += 10
            ly_do.append(f"Ký tự cuối '{pt['ky_tu_cuoi']}' chẵn → nghiêng Chẵn")
        else:
            diem_le += 10
            ly_do.append(f"Ký tự cuối '{pt['ky_tu_cuoi']}' lẻ → nghiêng Lẻ")

        if int(pt['ky_tu_dau'], 16) % 2 == 0:
            diem_chan += 5
            ly_do.append(f"Ký tự đầu '{pt['ky_tu_dau']}' chẵn → nghiêng Chẵn")
        else:
            diem_le += 5
            ly_do.append(f"Ký tự đầu '{pt['ky_tu_dau']}' lẻ → nghiêng Lẻ")

        if pt['so_nguyen'] % 2 == 0:
            diem_chan += 10
            ly_do.append("Số nguyên MD5 chẵn → nghiêng Chẵn")
        else:
            diem_le += 10
            ly_do.append("Số nguyên MD5 lẻ → nghiêng Lẻ")

        if diem_chan > diem_le:
            return {'ket_qua': 'CHẴN', 'do_tin_cay': min(diem_chan, 100), 'ly_do': ly_do, 'phan_tich': pt}
        elif diem_le > diem_chan:
            return {'ket_qua': 'LẺ', 'do_tin_cay': min(diem_le, 100), 'ly_do': ly_do, 'phan_tich': pt}
        else:
            if int(pt['ky_tu_cuoi'], 16) % 2 == 0:
                return {'ket_qua': 'CHẴN', 'do_tin_cay': 55, 'ly_do': ly_do + ["Hòa điểm, ưu tiên ký tự cuối"], 'phan_tich': pt}
            else:
                return {'ket_qua': 'LẺ', 'do_tin_cay': 55, 'ly_do': ly_do + ["Hòa điểm, ưu tiên ký tự cuối"], 'phan_tich': pt}

# ------------------------------------------------------------
# LƯU LỊCH SỬ DỰ ĐOÁN
# ------------------------------------------------------------
class LichSu:
    @staticmethod
    def doc():
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    @staticmethod
    def luu(ban_ghi):
        lich_su = LichSu.doc()
        lich_su.append(ban_ghi)
        if len(lich_su) > 200:
            lich_su = lich_su[-200:]
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(lich_su, f, ensure_ascii=False, indent=2)

# ------------------------------------------------------------
# BOT HANDLERS
# ------------------------------------------------------------
thuan_toan = ThuanToanDuDoan()
api = APIKwinstore()

def tao_menu_chinh():
    keyboard = [
        [InlineKeyboardButton("🎲 Tài Xỉu", callback_data="taixiu")],
        [InlineKeyboardButton("🎲 Sicbo", callback_data="sicbo")],
        [InlineKeyboardButton("📊 Dự Đoán TX", callback_data="dudoan")],
        [InlineKeyboardButton("📊 Dự Đoán Sicbo", callback_data="dudoan_sicbo")],
        [InlineKeyboardButton("📜 Lịch Sử TX", callback_data="lichsu_tx")],
        [InlineKeyboardButton("📜 Lịch Sử Sicbo", callback_data="lichsu_sicbo")],
        [InlineKeyboardButton("🔑 MD5 Chẵn Lẻ", callback_data="md5_help")],
        [InlineKeyboardButton("👑 Admin", callback_data="admin")],
        [InlineKeyboardButton("💰 Donate", callback_data="donate")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def lenh_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start — Tin nhắn chào mừng."""
    user = update.effective_user
    text = (
        f"╔═══════════════════════════════╗\n"
        f"║   🎲 *BOT DỰ ĐOÁN TÀI XỈU*   ║\n"
        f"║      *SIÊU VIP PRO MAX*       ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"👋 Chào *{user.first_name}*!\n\n"
        f"📊 *Tính năng chính:*\n"
        f"├ 🎯 Tài Xỉu — Sunwin Live\n"
        f"├ 🎲 Sicbo — Sunwin Live\n"
        f"├ 📈 Dự đoán TX (thuật toán cầu)\n"
        f"├ 📈 Dự đoán Sicbo\n"
        f"├ 📜 Lịch sử 20 ván gần nhất\n"
        f"└ 🔑 MD5 Chẵn Lẻ\n\n"
        f"📌 *Nguồn dữ liệu:* {ADMIN_USERNAME}\n"
        f"🧠 *Thuật toán:*\n"
        f"   • Phân tích cầu bệt\n"
        f"   • Cầu 1-1 (đảo chiều)\n"
        f"   • Tỷ lệ Tài/Xỉu\n"
        f"   • Markov chain\n\n"
        f"⚡ *Không random — Phân tích thật*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 Admin: {ADMIN_USERNAME}\n"
        f"💡 Gõ /help để xem tất cả lệnh\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👇 *Chọn chức năng:*"
    )
    await update.message.reply_text(
        text,
        reply_markup=tao_menu_chinh(),
        parse_mode="Markdown"
    )

async def lenh_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /help — Hướng dẫn sử dụng."""
    text = (
        f"📖 *HƯỚNG DẪN SỬ DỤNG BOT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 *Lệnh chính:*\n"
        f"├ `/start` — Khởi động bot\n"
        f"├ `/taixiu` — Kết quả TX mới nhất\n"
        f"├ `/sicbo` — Kết quả Sicbo mới nhất\n"
        f"├ `/dudoan` — Dự đoán Tài Xỉu\n"
        f"├ `/md5 <chuỗi>` — Dự đoán MD5\n"
        f"└ `/admin` — Liên hệ admin\n\n"
        f"📊 *Nút menu:*\n"
        f"├ 🎲 Tài Xỉu — Xem kết quả live\n"
        f"├ 🎲 Sicbo — Xem kết quả live\n"
        f"├ 📊 Dự Đoán TX — Phân tích cầu\n"
        f"├ 📊 Dự Đoán Sicbo — Phân tích cầu\n"
        f"├ 📜 Lịch Sử TX — 20 ván gần nhất\n"
        f"├ 📜 Lịch Sử Sicbo — 20 ván gần nhất\n"
        f"├ 🔑 MD5 Chẵn Lẻ — Nhập MD5\n"
        f"├ 👑 Admin — Liên hệ\n"
        f"└ 💰 Donate — Ủng hộ\n\n"
        f"💡 *Mẹo:* Gõ `T X T X T` (chuỗi kết quả) để bot phân tích cầu nhanh!\n\n"
        f"👑 Admin: {ADMIN_USERNAME}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def lenh_taixiu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Đang lấy kết quả Tài Xỉu...")
    kq = api.lay_tai_xiu()
    if not kq or "loi" in kq:
        await update.message.reply_text(f"❌ Lỗi: {kq.get('loi', 'Không lấy được dữ liệu')}")
        return
    text = (
        f"🎲 KẾT QUẢ TÀI XỈU\n\n"
        f"📌 Phiên: {kq['phien']}\n"
        f"⏰ Thời gian: {kq['thoi_gian']}\n"
        f"🎯 Kết quả: {kq['ket_qua']}\n"
        f"🔢 Tổng: {kq['tong']}\n"
        f"🎲 Xúc xắc: {kq['xuc_xac'][0]} - {kq['xuc_xac'][1]} - {kq['xuc_xac'][2]}\n"
    )
    await update.message.reply_text(text, reply_markup=tao_menu_chinh())

async def lenh_sicbo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Đang lấy kết quả Sicbo...")
    kq = api.lay_sicbo()
    if not kq or "loi" in kq:
        await update.message.reply_text(f"❌ Lỗi: {kq.get('loi', 'Không lấy được dữ liệu')}")
        return
    text = (
        f"🎲 KẾT QUẢ SICBO\n\n"
        f"📌 Phiên: {kq['phien']}\n"
        f"🎯 Kết quả: {kq['ket_qua']}\n"
        f"🔢 Tổng: {kq['tong']}\n"
        f"🎲 Xúc xắc: {kq['xuc_xac'][0]} - {kq['xuc_xac'][1]} - {kq['xuc_xac'][2]}\n"
        f"🔑 KeyR: {kq.get('keyR', '')}\n"
    )
    await update.message.reply_text(text, reply_markup=tao_menu_chinh())

async def lenh_dudoan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dự đoán Tài Xỉu — dùng API history."""
    await update.message.reply_text("⏳ Đang lấy lịch sử Tài Xỉu từ API...")
    lich_su = api.lay_lich_su_tai_xiu(20)
    if not lich_su:
        await update.message.reply_text("❌ Không lấy được lịch sử TX!")
        return

    danh_sach = [{"ket_qua": item["ket_qua"]} for item in lich_su]
    thuan_toan.nap_lich_su(danh_sach)
    ket_qua = thuan_toan.du_doan()
    ten = "TÀI" if ket_qua['ket_qua'] == 'T' else "XỈU"
    emoji = "🔴" if ket_qua['ket_qua'] == 'T' else "🔵"

    chuoi = ' '.join(thuan_toan.lich_su[:15])

    text = (
        f"{emoji} DỰ ĐOÁN TÀI XỈU: {ten}\n\n"
        f"📊 Độ tin cậy: {ket_qua['do_tin_cay']}%\n"
        f"📋 Chuỗi 15 ván: {chuoi}\n"
        f"📈 Tỷ lệ: Tài {thuan_toan.lich_su.count('T')}/{len(thuan_toan.lich_su)} | "
        f"Xỉu {thuan_toan.lich_su.count('X')}/{len(thuan_toan.lich_su)}\n\n"
        f"🔍 Lý do:\n"
    )
    for ly_do in ket_qua['ly_do'][:5]:
        text += f"• {ly_do}\n"

    LichSu.luu({
        'thoi_gian': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': update.effective_user.id,
        'loai': 'tx',
        'du_doan': ket_qua['ket_qua'],
        'do_tin_cay': ket_qua['do_tin_cay']
    })
    await update.message.reply_text(text, reply_markup=tao_menu_chinh())

async def lenh_md5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /md5 <chuỗi_32_ký_tự> - dự đoán chẵn lẻ."""
    if not context.args:
        await update.message.reply_text(
            "📝 Sử dụng: /md5 <chuỗi_32_ký_tự>\n"
            "Ví dụ: /md5 f2027d179b1791b821515bc59d1f7f44\n\n"
            "🔍 Bot sẽ phân tích chuỗi MD5 và dự đoán Chẵn/Lẻ."
        )
        return

    chuoi_md5 = context.args[0].strip().lower()
    if not re.fullmatch(r'[a-f0-9]{32}', chuoi_md5):
        await update.message.reply_text(
            "❌ Chuỗi không hợp lệ!\n"
            "📌 MD5 phải có đúng 32 ký tự, chỉ gồm 0-9 và a-f.\n"
            f"📌 Chuỗi bạn gửi có {len(chuoi_md5)} ký tự."
        )
        return

    thuan_toan_md5 = ThuanToanMD5(chuoi_md5)
    ket_qua = thuan_toan_md5.du_doan()
    if not ket_qua:
        await update.message.reply_text("❌ Lỗi phân tích MD5!")
        return

    emoji = "⚪" if ket_qua['ket_qua'] == "CHẴN" else "⚫"
    pt = ket_qua['phan_tich']

    text = (
        f"{emoji} DỰ ĐOÁN: {ket_qua['ket_qua']}\n\n"
        f"📊 Độ tin cậy: {ket_qua['do_tin_cay']}%\n"
        f"🔑 MD5: {chuoi_md5}\n"
        f"🔢 Số nguyên: {pt['so_nguyen']}\n"
        f"📈 Tổng hex: {pt['tong_hex']}\n"
        f"⚖️ Chẵn/Lẻ: {pt['so_chan']}/{pt['so_le']}\n\n"
        f"🔍 Lý do:\n"
    )
    for ly in ket_qua['ly_do'][:6]:
        text += f"• {ly}\n"

    await update.message.reply_text(text)

async def lenh_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👑 ADMIN\n📱 Telegram: {ADMIN_USERNAME}"
    )

async def lenh_donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 DONATE\nSTK: 08779466881\nNGUYEN TUAN HUNG - MB Bank"
    )

async def xu_ly_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "taixiu":
        kq = api.lay_tai_xiu()
        if kq and "ket_qua" in kq:
            text = (
                f"🎲 TÀI XỈU MỚI NHẤT\n\n"
                f"📌 Phiên: {kq['phien']}\n"
                f"⏰ {kq['thoi_gian']}\n"
                f"🎯 {kq['ket_qua']} - Tổng: {kq['tong']}\n"
                f"🎲 {kq['xuc_xac'][0]}-{kq['xuc_xac'][1]}-{kq['xuc_xac'][2]}"
            )
            await query.edit_message_text(text, reply_markup=tao_menu_chinh())
        else:
            await query.edit_message_text("❌ Không lấy được dữ liệu!", reply_markup=tao_menu_chinh())

    elif data == "sicbo":
        kq = api.lay_sicbo()
        if kq and "ket_qua" in kq:
            text = (
                f"🎲 SICBO MỚI NHẤT\n\n"
                f"📌 Phiên: {kq['phien']}\n"
                f"🎯 {kq['ket_qua']} - Tổng: {kq['tong']}\n"
                f"🎲 {kq['xuc_xac'][0]}-{kq['xuc_xac'][1]}-{kq['xuc_xac'][2]}"
            )
            await query.edit_message_text(text, reply_markup=tao_menu_chinh())
        else:
            await query.edit_message_text("❌ Không lấy được dữ liệu!", reply_markup=tao_menu_chinh())

    elif data == "dudoan":
        await query.edit_message_text("⏳ Đang phân tích Tài Xỉu...")
        lich_su = api.lay_lich_su_tai_xiu(20)
        if lich_su:
            danh_sach = [{"ket_qua": item["ket_qua"]} for item in lich_su]
            thuan_toan.nap_lich_su(danh_sach)
            ket_qua = thuan_toan.du_doan()
            ten = "TÀI" if ket_qua['ket_qua'] == 'T' else "XỈU"
            emoji = "🔴" if ket_qua['ket_qua'] == 'T' else "🔵"
            chuoi = ' '.join(thuan_toan.lich_su[:15])
            text = (
                f"{emoji} DỰ ĐOÁN TX: {ten}\n"
                f"📊 Độ tin cậy: {ket_qua['do_tin_cay']}%\n"
                f"📋 Chuỗi: {chuoi}\n\n"
                f"🔍 Lý do:\n"
            )
            for ly_do in ket_qua['ly_do'][:5]:
                text += f"• {ly_do}\n"
            await query.edit_message_text(text, reply_markup=tao_menu_chinh())
        else:
            await query.edit_message_text("❌ Không lấy được lịch sử!", reply_markup=tao_menu_chinh())

    elif data == "dudoan_sicbo":
        await query.edit_message_text("⏳ Đang phân tích Sicbo...")
        lich_su = api.lay_lich_su_sicbo(20)
        if lich_su:
            danh_sach = [{"ket_qua": item["ket_qua"]} for item in lich_su]
            thuan_toan.nap_lich_su(danh_sach)
            ket_qua = thuan_toan.du_doan()
            ten = "TÀI" if ket_qua['ket_qua'] == 'T' else "XỈU"
            emoji = "🔴" if ket_qua['ket_qua'] == 'T' else "🔵"
            chuoi = ' '.join(thuan_toan.lich_su[:15])
            text = (
                f"{emoji} DỰ ĐOÁN SICBO: {ten}\n"
                f"📊 Độ tin cậy: {ket_qua['do_tin_cay']}%\n"
                f"📋 Chuỗi: {chuoi}\n\n"
                f"🔍 Lý do:\n"
            )
            for ly_do in ket_qua['ly_do'][:5]:
                text += f"• {ly_do}\n"
            await query.edit_message_text(text, reply_markup=tao_menu_chinh())
        else:
            await query.edit_message_text("❌ Không lấy được lịch sử Sicbo!", reply_markup=tao_menu_chinh())

    elif data == "lichsu_tx":
        lich_su = api.lay_lich_su_tai_xiu(20)
        if not lich_su:
            await query.edit_message_text("📜 Không lấy được lịch sử TX.", reply_markup=tao_menu_chinh())
            return
        text = "📜 LỊCH SỬ TÀI XỈU (20 ván gần nhất):\n\n"
        for item in lich_su[:20]:
            emoji = "🔴" if "tài" in item['ket_qua'].lower() else "🔵"
            text += f"{emoji} Phiên {item['phien']}: {item['ket_qua']} (Tổng {item['tong']})\n"
        await query.edit_message_text(text, reply_markup=tao_menu_chinh())

    elif data == "lichsu_sicbo":
        lich_su = api.lay_lich_su_sicbo(20)
        if not lich_su:
            await query.edit_message_text("📜 Không lấy được lịch sử Sicbo.", reply_markup=tao_menu_chinh())
            return
        text = "📜 LỊCH SỬ SICBO (20 ván gần nhất):\n\n"
        for item in lich_su[:20]:
            emoji = "🔴" if "tài" in item['ket_qua'].lower() else "🔵"
            text += f"{emoji} Phiên {item['phien']}: {item['ket_qua']} (Tổng {item['tong']})\n"
        await query.edit_message_text(text, reply_markup=tao_menu_chinh())

    elif data == "md5_help":
        await query.edit_message_text(
            "🔑 DỰ ĐOÁN MD5 CHẴN LẺ\n\n"
            "Sử dụng: /md5 <chuỗi_32_ký_tự>\n"
            "Ví dụ: /md5 f2027d179b1791b821515bc59d1f7f44\n\n"
            "Bot sẽ phân tích:\n"
            "• Tổng giá trị hex\n"
            "• Số ký tự chẵn/lẻ\n"
            "• Ký tự đầu/cuối\n"
            "• Số nguyên MD5\n"
            "→ Dự đoán CHẴN hoặc LẺ kèm độ tin cậy.",
            reply_markup=tao_menu_chinh()
        )

    elif data == "admin":
        await query.edit_message_text(
            f"👑 ADMIN\n📱 Telegram: {ADMIN_USERNAME}",
            reply_markup=tao_menu_chinh()
        )

    elif data == "donate":
        await query.edit_message_text(
            "💰 DONATE\nSTK: 08779466881\nNGUYEN TUAN HUNG - MB Bank",
            reply_markup=tao_menu_chinh()
        )

async def xu_ly_tin_nhan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    danh_sach = [arg for arg in text.split() if arg in ['T', 'X']]
    if len(danh_sach) >= 3:
        thuan_toan.nap_lich_su([{'ket_qua': 'Tài' if kq == 'T' else 'Xỉu'} for kq in danh_sach])
        ket_qua = thuan_toan.du_doan()
        ten = "TÀI" if ket_qua['ket_qua'] == 'T' else "XỈU"
        emoji = "🔴" if ket_qua['ket_qua'] == 'T' else "🔵"
        reply = f"{emoji} DỰ ĐOÁN: {ten}\n📊 Độ tin cậy: {ket_qua['do_tin_cay']}%\n\n🔍 Lý do:\n"
        for ly_do in ket_qua['ly_do'][:5]:
            reply += f"• {ly_do}\n"
        await update.message.reply_text(reply, reply_markup=tao_menu_chinh())
    else:
        await update.message.reply_text("📋 Dùng menu để chọn chức năng.", reply_markup=tao_menu_chinh())

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Chưa cấu hình BOT_TOKEN!")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", lenh_start))
    application.add_handler(CommandHandler("help", lenh_help))
    application.add_handler(CommandHandler("taixiu", lenh_taixiu))
    application.add_handler(CommandHandler("sicbo", lenh_sicbo))
    application.add_handler(CommandHandler("dudoan", lenh_dudoan))
    application.add_handler(CommandHandler("md5", lenh_md5))
    application.add_handler(CommandHandler("admin", lenh_admin))
    application.add_handler(CommandHandler("donate", lenh_donate))
    application.add_handler(CallbackQueryHandler(xu_ly_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, xu_ly_tin_nhan))

    print("🎲 Bot Dự Đoán Tài Xỉu + Sicbo + MD5 đang chạy...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()