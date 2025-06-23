// 로그 레벨 관리 유틸리티
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4
}

class Logger {
  private static instance: Logger;
  private logLevel: LogLevel;

  private constructor() {
    // 개발환경에서는 DEBUG, 프로덕션에서는 ERROR만
    this.logLevel = import.meta.env.DEV ? LogLevel.DEBUG : LogLevel.ERROR;
  }

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  setLogLevel(level: LogLevel) {
    this.logLevel = level;
  }

  debug(message: string, ...args: any[]) {
    if (this.logLevel <= LogLevel.DEBUG) {
      console.log(`🔧 ${message}`, ...args);
    }
  }

  info(message: string, ...args: any[]) {
    if (this.logLevel <= LogLevel.INFO) {
      console.log(`ℹ️ ${message}`, ...args);
    }
  }

  warn(message: string, ...args: any[]) {
    if (this.logLevel <= LogLevel.WARN) {
      console.warn(`⚠️ ${message}`, ...args);
    }
  }

  error(message: string, ...args: any[]) {
    if (this.logLevel <= LogLevel.ERROR) {
      console.error(`❌ ${message}`, ...args);
    }
  }

  success(message: string, ...args: any[]) {
    if (this.logLevel <= LogLevel.INFO) {
      console.log(`✅ ${message}`, ...args);
    }
  }

  auth(message: string, ...args: any[]) {
    if (this.logLevel <= LogLevel.DEBUG) {
      console.log(`🔐 ${message}`, ...args);
    }
  }

  router(message: string, ...args: any[]) {
    if (this.logLevel <= LogLevel.DEBUG) {
      console.log(`🛣️ ${message}`, ...args);
    }
  }

  api(message: string, ...args: any[]) {
    if (this.logLevel <= LogLevel.DEBUG) {
      console.log(`📡 ${message}`, ...args);
    }
  }
}

export const logger = Logger.getInstance();
