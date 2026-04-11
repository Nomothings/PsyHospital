/**
 * LoginPage 组件
 * 登录 / 注册页面 — 毛玻璃特效
 */
const LoginPage = {
    template: `
        <div class="login-page">
            <!-- 背景图 -->
            <div class="login-page__bg"></div>

            <!-- 装饰粒子 -->
            <div class="login-page__orb" style="width:300px;height:300px;top:-80px;right:-60px;"></div>
            <div class="login-page__orb" style="width:250px;height:250px;bottom:-60px;left:-80px;"></div>
            <div class="login-page__orb" style="width:150px;height:150px;top:50%;right:20%;"></div>

            <!-- 毛玻璃卡片 -->
            <div class="login-card">
                <!-- Logo / 标题 -->
                <div class="login-card__header">
                    <div class="login-card__logo">
                        <el-icon :size="48" color="#5ed6c8"><FirstAidKit /></el-icon>
                    </div>
                    <h1 class="login-card__title">Mental Hospital</h1>
                    <p class="login-card__subtitle">
                        精神科访谈训练系统
                    </p>
                </div>

                <!-- Tab 切换 -->
                <div class="login-card__tabs">
                    <div class="login-card__tab"
                         :class="{ active: !isRegister }"
                         @click="isRegister = false">
                        登录
                    </div>
                    <div class="login-card__tab"
                         :class="{ active: isRegister }"
                         @click="isRegister = true">
                        注册
                    </div>
                </div>

                <!-- 登录表单 -->
                <el-form v-if="!isRegister"
                         :model="loginForm"
                         :rules="loginRules"
                         ref="loginFormRef"
                         class="login-card__form">
                    <el-form-item prop="username">
                        <el-input v-model="loginForm.username"
                                  placeholder="用户名 / 邮箱"
                                  :prefix-icon="User"
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-form-item prop="password">
                        <el-input v-model="loginForm.password"
                                  type="password"
                                  placeholder="密码"
                                  :prefix-icon="Lock"
                                  show-password
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <div class="login-card__actions">
                        <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
                        <el-link type="primary" :underline="false" style="font-size:13px;">
                            忘记密码？
                        </el-link>
                    </div>
                    <el-button type="primary"
                               size="large"
                               class="login-card__submit"
                               @click="handleLogin"
                               :loading="loading">
                        登 录
                    </el-button>
                </el-form>

                <!-- 注册表单 -->
                <el-form v-else
                         :model="registerForm"
                         :rules="registerRules"
                         ref="registerFormRef"
                         class="login-card__form">
                    <el-form-item prop="username">
                        <el-input v-model="registerForm.username"
                                  placeholder="用户名"
                                  :prefix-icon="User"
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-form-item prop="email">
                        <el-input v-model="registerForm.email"
                                  type="email"
                                  placeholder="邮箱地址"
                                  :prefix-icon="Message"
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-form-item prop="password">
                        <el-input v-model="registerForm.password"
                                  type="password"
                                  placeholder="密码"
                                  :prefix-icon="Lock"
                                  show-password
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-form-item prop="confirmPassword">
                        <el-input v-model="registerForm.confirmPassword"
                                  type="password"
                                  placeholder="确认密码"
                                  :prefix-icon="Lock"
                                  show-password
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-button type="primary"
                               size="large"
                               class="login-card__submit"
                               @click="handleRegister"
                               :loading="loading">
                        注 册
                    </el-button>
                </el-form>

                <!-- 底部信息 -->
                <div class="login-card__footer">
                    <span class="login-card__footer-text">
                        {{ isRegister ? '已有账户？' : '还没有账户？' }}
                        <el-link type="primary" :underline="false" @click="isRegister = !isRegister">
                            {{ isRegister ? '立即登录' : '立即注册' }}
                        </el-link>
                    </span>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            isRegister: false,
            loading: false,

            loginForm: {
                username: '',
                password: '',
                remember: false,
            },

            registerForm: {
                username: '',
                email: '',
                password: '',
                confirmPassword: '',
            },

            loginRules: {
                username: [
                    { required: true, message: '请输入用户名', trigger: 'blur' },
                    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' },
                ],
                password: [
                    { required: true, message: '请输入密码', trigger: 'blur' },
                    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
                ],
            },

            registerRules: {
                username: [
                    { required: true, message: '请输入用户名', trigger: 'blur' },
                    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' },
                ],
                email: [
                    { required: true, message: '请输入邮箱', trigger: 'blur' },
                    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
                ],
                password: [
                    { required: true, message: '请输入密码', trigger: 'blur' },
                    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
                ],
                confirmPassword: [
                    { required: true, message: '请确认密码', trigger: 'blur' },
                    {
                        validator: (rule, value, callback) => {
                            if (value !== this.registerForm.password) {
                                callback(new Error('两次密码不一致'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'blur',
                    },
                ],
            },
        };
    },

    computed: {
        User() { return ElementPlusIconsVue.User; },
        Lock() { return ElementPlusIconsVue.Lock; },
        Message() { return ElementPlusIconsVue.Message; },
        FirstAidKit() { return ElementPlusIconsVue.FirstAidKit; },
    },

    methods: {
        handleLogin() {
            this.loading = true;
            // 无需校验，直接进入问诊
            setTimeout(() => {
                this.loading = false;
                this.$router.push('/patients');
                this.$message.success('欢迎回来');
            }, 800);
        },

        handleRegister() {
            this.$refs.registerFormRef.validate((valid) => {
                if (valid) {
                    this.loading = true;
                    // TODO: 调用注册 API
                    setTimeout(() => {
                        this.loading = false;
                        this.isRegister = false;
                        this.$message.success('注册成功，请登录');
                    }, 1000);
                }
            });
        },
    },
};
