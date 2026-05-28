const LoginPage = {
    template: `
        <div class="login-page">
            <div class="login-page__bg"></div>

            <div class="login-page__orb" style="width:300px;height:300px;top:-80px;right:-60px;"></div>
            <div class="login-page__orb" style="width:250px;height:250px;bottom:-60px;left:-80px;"></div>
            <div class="login-page__orb" style="width:150px;height:150px;top:50%;right:20%;"></div>

            <div class="login-card">
                <div class="login-card__header">
                    <div class="login-card__logo">
                        <el-icon :size="48" color="#5ed6c8"><FirstAidKit /></el-icon>
                    </div>
                    <h1 class="login-card__title">Mental Hospital</h1>
                    <p class="login-card__subtitle">
                        Psychiatry AI Simulated Interview & Training Platform
                    </p>
                </div>

                <div class="login-card__tabs">
                    <div class="login-card__tab"
                         :class="{ active: !isRegister }"
                         @click="isRegister = false">
                        Login
                    </div>
                    <div class="login-card__tab"
                         :class="{ active: isRegister }"
                         @click="isRegister = true">
                        Register
                    </div>
                </div>

                <el-form v-if="!isRegister"
                         :model="loginForm"
                         :rules="loginRules"
                         ref="loginFormRef"
                         class="login-card__form">
                    <el-form-item prop="username">
                        <el-input v-model="loginForm.username"
                                  placeholder="Username / Email"
                                  :prefix-icon="User"
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-form-item prop="password">
                        <el-input v-model="loginForm.password"
                                  type="password"
                                  placeholder="Password"
                                  :prefix-icon="Lock"
                                  show-password
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <div class="login-card__actions">
                        <el-checkbox v-model="loginForm.remember">Remember me</el-checkbox>
                        <el-link type="primary" :underline="false" style="font-size:13px;">
                            Forgot password?
                        </el-link>
                    </div>
                    <el-button type="primary"
                               size="large"
                               class="login-card__submit"
                               @click="handleLogin"
                               :loading="loading">
                        Login
                    </el-button>
                </el-form>

                <el-form v-else
                         :model="registerForm"
                         :rules="registerRules"
                         ref="registerFormRef"
                         class="login-card__form">
                    <el-form-item prop="username">
                        <el-input v-model="registerForm.username"
                                  placeholder="Username"
                                  :prefix-icon="User"
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-form-item prop="email">
                        <el-input v-model="registerForm.email"
                                  type="email"
                                  placeholder="Email"
                                  :prefix-icon="Message"
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-form-item prop="password">
                        <el-input v-model="registerForm.password"
                                  type="password"
                                  placeholder="Password"
                                  :prefix-icon="Lock"
                                  show-password
                                  size="large"
                                  class="login-input" />
                    </el-form-item>
                    <el-form-item prop="confirmPassword">
                        <el-input v-model="registerForm.confirmPassword"
                                  type="password"
                                  placeholder="Confirm Password"
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
                        Register
                    </el-button>
                </el-form>

                <div class="login-card__footer">
                    <span class="login-card__footer-text">
                        {{ isRegister ? 'Already have an account?' : "Don't have an account?" }}
                        <el-link type="primary" :underline="false" @click="isRegister = !isRegister">
                            {{ isRegister ? 'Back to Login' : 'Register Now' }}
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
                    { required: true, message: 'Please enter username or email', trigger: 'blur' },
                    { min: 3, max: 20, message: 'Username must be 3-20 characters', trigger: 'blur' },
                ],
                password: [
                    { required: true, message: 'Please enter password', trigger: 'blur' },
                    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
                ],
            },

            registerRules: {
                username: [
                    { required: true, message: 'Please enter username', trigger: 'blur' },
                    { min: 3, max: 20, message: 'Username must be 3-20 characters', trigger: 'blur' },
                ],
                email: [
                    { required: true, message: 'Please enter email', trigger: 'blur' },
                    { type: 'email', message: 'Please enter a valid email format', trigger: 'blur' },
                ],
                password: [
                    { required: true, message: 'Please enter password', trigger: 'blur' },
                    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
                ],
                confirmPassword: [
                    { required: true, message: 'Please confirm password', trigger: 'blur' },
                    {
                        validator: (rule, value, callback) => {
                            if (value !== this.registerForm.password) {
                                callback(new Error('Passwords do not match'));
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
            this.$refs.loginFormRef.validate((valid) => {
                if (!valid) return;

                this.loading = true;
                setTimeout(() => {
                    this.loading = false;
                    const validAccounts = {
                        admin: 'admin123',
                        test1: '666666',
                    };
                    const accountName = this.loginForm.username;
                    if (validAccounts[accountName] && validAccounts[accountName] === this.loginForm.password) {
                        this.$router.push('/patients');
                        this.$message.success('Login successful');
                    } else {
                        this.$message.error('Invalid username or password');
                    }
                }, 800);
            });
        },

        handleRegister() {
            this.$refs.registerFormRef.validate((valid) => {
                if (valid) {
                    this.loading = true;
                    setTimeout(() => {
                        this.loading = false;
                        this.isRegister = false;
                        this.$message.success('Registration successful, please login');
                    }, 1000);
                }
            });
        },
    },
};
