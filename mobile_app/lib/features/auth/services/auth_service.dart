import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';

class AuthService {
  final ApiClient _apiClient;

  AuthService(this._apiClient);

  Future<void> sendOtp(String phone, String role) async {
    try {
      // Mocking API call: POST /auth/send-otp
      // await _apiClient.client.post('/auth/send-otp', data: {'phone': phone, 'role': role});
      await Future.delayed(const Duration(seconds: 1)); // Simulate network latency
    } on DioException catch (e) {
      throw Exception('Failed to send OTP: ${e.message}');
    }
  }

  Future<String> verifyOtp(String phone, String otp, String role) async {
    try {
      // Mocking API call: POST /auth/verify-otp
      // final response = await _apiClient.client.post('/auth/verify-otp', data: {'phone': phone, 'otp': otp, 'role': role});
      // return response.data['token'];
      await Future.delayed(const Duration(seconds: 1));
      if (otp == '1234') {
        return 'mock_jwt_token_for_$role';
      } else {
        throw Exception('Invalid OTP');
      }
    } on DioException catch (e) {
      throw Exception('Failed to verify OTP: ${e.message}');
    }
  }

  Future<void> logout() async {
    try {
      // Mocking API call: POST /auth/logout
      // await _apiClient.client.post('/auth/logout');
      await Future.delayed(const Duration(milliseconds: 500));
    } on DioException catch (e) {
      throw Exception('Failed to logout: ${e.message}');
    }
  }
}
