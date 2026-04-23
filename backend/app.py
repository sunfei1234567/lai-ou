from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///leio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# QQ邮箱配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 587,
    'sender_email': '2770894499@qq.com',  # 请修改为你的QQ邮箱
    'sender_password': 'akxinulcdewkdcjd',  # 授权码
    'admin_email': '1953680281@qq.com'  # 接收通知的管理员邮箱
}

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== 数据库模型 ====================

class Case(db.Model):
    """案例模型"""
    __tablename__ = 'cases'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # 标题
    category = db.Column(db.String(100), nullable=False)  # 行业/分类
    description = db.Column(db.Text, nullable=False)  # 简短描述
    content = db.Column(db.Text, nullable=False)  # 详细内容
    image_url = db.Column(db.String(500))  # 封面图片
    country = db.Column(db.String(100))  # 国家
    project_date = db.Column(db.String(50))  # 时间
    is_featured = db.Column(db.Boolean, default=False)  # 是否精选
    sort_order = db.Column(db.Integer, default=0)  # 排序
    status = db.Column(db.Integer, default=1)  # 1: 显示, 0: 隐藏
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'content': self.content,
            'image_url': self.image_url,
            'country': self.country,
            'project_date': self.project_date,
            'is_featured': self.is_featured,
            'sort_order': self.sort_order,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Consultation(db.Model):
    """客户咨询留言模型"""
    __tablename__ = 'consultations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    company = db.Column(db.String(200))
    service_type = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Integer, default=0)  # 0: 未处理, 1: 已处理, 2: 已跟进
    admin_remark = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'company': self.company,
            'service_type': self.service_type,
            'message': self.message,
            'status': self.status,
            'admin_remark': self.admin_remark,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Admin(db.Model):
    """管理员模型"""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Setting(db.Model):
    """系统配置表"""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @staticmethod
    def get(key, default=None):
        """获取配置值"""
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value, description=None):
        """设置配置值"""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()


# ==================== 邮件服务 ====================

def send_email_notification(subject, body, to_email=None):
    """发送邮件通知"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = to_email or EMAIL_CONFIG['admin_email']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False


def send_consultation_notification(consultation):
    """发送新咨询通知邮件"""
    subject = f"【徕欧科技】收到新的客户咨询 - {consultation.name}"
    body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px; background: #fafafa;">
        <div style="background: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <h2 style="color: #1a1a1a; font-size: 20px; font-weight: 500; margin-bottom: 24px; border-bottom: 1px solid #eee; padding-bottom: 16px;">
                收到新的客户咨询
            </h2>
            
            <table style="width: 100%; border-collapse: collapse; font-size: 14px; line-height: 1.8; color: #333;">
                <tr>
                    <td style="padding: 8px 0; color: #666; width: 80px;">姓名</td>
                    <td style="padding: 8px 0; font-weight: 500;">{consultation.name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666;">电话</td>
                    <td style="padding: 8px 0; font-weight: 500;">{consultation.phone}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666;">邮箱</td>
                    <td style="padding: 8px 0;">{consultation.email or '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666;">公司</td>
                    <td style="padding: 8px 0;">{consultation.company or '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666;">服务类型</td>
                    <td style="padding: 8px 0;">{consultation.service_type or '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666; vertical-align: top;">留言</td>
                    <td style="padding: 8px 0; background: #f5f5f5; padding: 12px; border-radius: 4px;">{consultation.message}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666;">提交时间</td>
                    <td style="padding: 8px 0;">{consultation.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
            
            <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee; text-align: center;">
                <a href="http://your-domain.com/admin/consultations" style="display: inline-block; padding: 12px 32px; background: #1a1a1a; color: #fff; text-decoration: none; border-radius: 4px; font-size: 14px;">
                    查看详情
                </a>
            </div>
        </div>
        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
            徕欧科技管理系统自动发送
        </p>
    </div>
    """
    return send_email_notification(subject, body)


# ==================== Case API ====================

@app.route('/api/cases', methods=['GET'])
def get_cases():
    """获取案例列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category = request.args.get('category')
    status = request.args.get('status', type=int)
    keyword = request.args.get('keyword')
    
    query = Case.query
    
    if category:
        query = query.filter(Case.category == category)
    if status is not None:
        query = query.filter(Case.status == status)
    if keyword:
        query = query.filter(Case.title.contains(keyword))
    
    pagination = query.order_by(Case.sort_order.desc(), Case.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'code': 200,
        'data': {
            'items': [case.to_dict() for case in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@app.route('/api/cases/<int:case_id>', methods=['GET'])
def get_case(case_id):
    """获取案例详情"""
    case = Case.query.get_or_404(case_id)
    return jsonify({
        'code': 200,
        'data': case.to_dict()
    })


@app.route('/api/cases', methods=['POST'])
@login_required
def create_case():
    """创建案例"""
    data = request.get_json()

    case = Case(
        title=data.get('title'),
        category=data.get('category'),
        description=data.get('description'),
        content=data.get('content'),
        image_url=data.get('image_url'),
        country=data.get('country'),
        project_date=data.get('project_date'),
        is_featured=data.get('is_featured', False),
        sort_order=data.get('sort_order', 0),
        status=data.get('status', 1)
    )
    
    db.session.add(case)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': case.to_dict()
    })


@app.route('/api/cases/<int:case_id>', methods=['PUT'])
@login_required
def update_case(case_id):
    """更新案例"""
    case = Case.query.get_or_404(case_id)
    data = request.get_json()

    case.title = data.get('title', case.title)
    case.category = data.get('category', case.category)
    case.description = data.get('description', case.description)
    case.content = data.get('content', case.content)
    case.image_url = data.get('image_url', case.image_url)
    case.country = data.get('country', case.country)
    case.project_date = data.get('project_date', case.project_date)
    case.is_featured = data.get('is_featured', case.is_featured)
    case.sort_order = data.get('sort_order', case.sort_order)
    case.status = data.get('status', case.status)
    case.updated_at = datetime.now()
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': case.to_dict()
    })


@app.route('/api/cases/<int:case_id>', methods=['DELETE'])
@login_required
def delete_case(case_id):
    """删除案例"""
    case = Case.query.get_or_404(case_id)
    db.session.delete(case)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# ==================== Consultation API ====================

@app.route('/api/consultations', methods=['GET'])
@login_required
def get_consultations():
    """获取咨询列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', type=int)
    keyword = request.args.get('keyword')
    
    query = Consultation.query
    
    if status is not None:
        query = query.filter(Consultation.status == status)
    if keyword:
        query = query.filter(
            db.or_(
                Consultation.name.contains(keyword),
                Consultation.phone.contains(keyword),
                Consultation.message.contains(keyword)
            )
        )
    
    pagination = query.order_by(Consultation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 统计
    stats = {
        'total': Consultation.query.count(),
        'pending': Consultation.query.filter_by(status=0).count(),
        'processed': Consultation.query.filter_by(status=1).count(),
        'followed': Consultation.query.filter_by(status=2).count()
    }
    
    return jsonify({
        'code': 200,
        'data': {
            'items': [c.to_dict() for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'stats': stats
        }
    })


@app.route('/api/consultations/<int:consultation_id>', methods=['GET'])
@login_required
def get_consultation(consultation_id):
    """获取咨询详情"""
    consultation = Consultation.query.get_or_404(consultation_id)
    return jsonify({
        'code': 200,
        'data': consultation.to_dict()
    })


@app.route('/api/consultations', methods=['POST'])
def create_consultation():
    """创建咨询（前台提交）"""
    data = request.get_json()
    
    consultation = Consultation(
        name=data.get('name'),
        phone=data.get('phone'),
        email=data.get('email'),
        company=data.get('company'),
        service_type=data.get('service_type'),
        message=data.get('message'),
        ip_address=request.remote_addr,
        status=0
    )
    
    db.session.add(consultation)
    db.session.commit()
    
    # 发送邮件通知
    send_consultation_notification(consultation)
    
    return jsonify({
        'code': 200,
        'message': '提交成功，我们会尽快与您联系'
    })


@app.route('/api/consultations/<int:consultation_id>', methods=['PUT'])
@login_required
def update_consultation(consultation_id):
    """更新咨询状态"""
    consultation = Consultation.query.get_or_404(consultation_id)
    data = request.get_json()
    
    consultation.status = data.get('status', consultation.status)
    consultation.admin_remark = data.get('admin_remark', consultation.admin_remark)
    consultation.updated_at = datetime.now()
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': consultation.to_dict()
    })


@app.route('/api/consultations/<int:consultation_id>', methods=['DELETE'])
@login_required
def delete_consultation(consultation_id):
    """删除咨询"""
    consultation = Consultation.query.get_or_404(consultation_id)
    db.session.delete(consultation)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# ==================== 后台管理页面 ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')


@app.route('/admin/logout')
def admin_logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('admin_login'))


@app.route('/admin')
@login_required
def admin_dashboard():
    """后台首页"""
    stats = {
        'cases_count': Case.query.count(),
        'consultations_count': Consultation.query.count(),
        'pending_consultations': Consultation.query.filter_by(status=0).count(),
        'featured_cases': Case.query.filter_by(is_featured=True).count()
    }
    email_notification_enabled = Setting.get('email_notification_enabled', 'false')
    return render_template('dashboard.html', stats=stats, email_notification_enabled=email_notification_enabled)


@app.route('/admin/cases')
@login_required
def admin_cases():
    """案例管理页面"""
    return render_template('cases.html')


@app.route('/admin/consultations')
@login_required
def admin_consultations():
    """咨询管理页面"""
    return render_template('consultations.html')


@app.route('/api/settings/email_notification', methods=['POST'])
@login_required
def update_email_notification():
    """更新邮件通知设置"""
    data = request.get_json()
    enabled = data.get('enabled', False)
    
    Setting.set(
        'email_notification_enabled', 
        'true' if enabled else 'false',
        '是否开启新咨询邮件通知'
    )
    
    return jsonify({
        'code': 200,
        'message': '设置已更新'
    })


@app.route('/')
def index():
    """根路径重定向到后台登录页"""
    return redirect(url_for('admin_login'))


# ==================== 初始化 ====================

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()

        # 创建默认管理员
        if not Admin.query.filter_by(username='admin').first():
            hashed_password = generate_password_hash('admin123')
            admin = Admin(username='admin', password=hashed_password)
            db.session.add(admin)
            db.session.commit()
            print("默认管理员已创建: admin / admin123")

        # 默认开启邮件通知
        if not Setting.query.filter_by(key='email_notification_enabled').first():
            Setting.set(
                'email_notification_enabled',
                'true',
                '是否开启新咨询邮件通知'
            )
            print("邮件通知已默认开启")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=10000)
