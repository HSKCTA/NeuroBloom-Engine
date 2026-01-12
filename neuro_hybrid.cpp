#include <zmq.h>
#include <iostream>
#include <string.h>
#include <unistd.h>
#include <chrono>
#include <math.h>

// OpenCV Headers
#include <opencv2/opencv.hpp>
#include <opencv2/objdetect.hpp>

// OpenSSL Headers
#include <openssl/evp.h>
#include <openssl/aes.h>
#include <openssl/buffer.h>
#include <openssl/bio.h>

// --- CONFIG ---
#define ZMQ_PORT "tcp://*:5555"
const unsigned char MY_AES_KEY[] = "01234567890123456789012345678901"; 
const unsigned char AES_IV[]  = "0123456789012345"; 

// --- HELPER: Base64 & AES ---
char* base64_encode(const unsigned char* input, int length) {
    BIO *bmem, *b64; BUF_MEM *bptr;
    b64 = BIO_new(BIO_f_base64()); BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL);
    bmem = BIO_new(BIO_s_mem()); b64 = BIO_push(b64, bmem);
    BIO_write(b64, input, length); BIO_flush(b64); BIO_get_mem_ptr(b64, &bptr);
    char* buff = (char*)malloc(bptr->length + 1);
    memcpy(buff, bptr->data, bptr->length); buff[bptr->length] = 0;
    BIO_free_all(b64); return buff;
}

int encrypt_aes(const unsigned char *plaintext, int plaintext_len, 
                const unsigned char *key, const unsigned char *iv, unsigned char *ciphertext) {
    EVP_CIPHER_CTX *ctx; int len, clen;
    if(!(ctx = EVP_CIPHER_CTX_new())) return -1;
    EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv);
    EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, plaintext_len); clen = len;
    EVP_EncryptFinal_ex(ctx, ciphertext + len, &len); clen += len;
    EVP_CIPHER_CTX_free(ctx); return clen;
}

long long current_timestamp() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
}

double pink_noise(double &state) {
    double white = ((rand() % 1000) / 1000.0) - 0.5;
    state = 0.95 * state + 0.05 * white; 
    return state * 10.0;
}

double jitter(double base, double variance) {
    return base + (rand() % (int)variance) - (variance / 2);
}

double get_eye_gaze_offset(cv::Mat &eye_roi) {
    if (eye_roi.empty()) return 1.0; 
    cv::Mat gray_eye;
    cv::cvtColor(eye_roi, gray_eye, cv::COLOR_BGR2GRAY);
    cv::equalizeHist(gray_eye, gray_eye); 
    cv::Point minLoc; 
    double minVal;
    cv::minMaxLoc(gray_eye, &minVal, NULL, &minLoc, NULL);
    double center_x = (double)gray_eye.cols / 2.0;
    double offset = abs(minLoc.x - center_x) / center_x; 
    cv::drawMarker(eye_roi, minLoc, cv::Scalar(0, 0, 255), cv::MARKER_CROSS, 5);
    return offset;
}

int main() {
    std::cout << "[SYSTEM] Starting NeuroBloom Ultimate Engine (Academic Features)..." << std::endl;

    void *context = zmq_ctx_new();
    void *publisher = zmq_socket(context, ZMQ_PUB);
    int linger = 0; zmq_setsockopt(publisher, ZMQ_LINGER, &linger, sizeof(linger));
    zmq_bind(publisher, ZMQ_PORT);

    // CAMERA SETUP (Webcam IP)
    std::string camera_url = "http://10.241.90.50:8080/video"; 
    cv::VideoCapture cap(camera_url);
    
    cv::CascadeClassifier face_cascade, eye_cascade;
    if(!face_cascade.load("haarcascade_frontalface_default.xml")) std::cerr << "No Face XML" << std::endl;
    if(!eye_cascade.load("haarcascade_eye.xml")) std::cerr << "No Eye XML" << std::endl;

    // STATE VARIABLES
    double last_yaw = 0;
    double noise_state = 0;
    
    // Feature Accumulators
    long total_frames = 0;
    long focused_frames = 0;
    int blink_counter = 0;
    bool eyes_were_closed = false;

    // 8-Band State
    double delta, theta, low_alpha, high_alpha, low_beta, high_beta, low_gamma, mid_gamma;

    while (1) {
        cv::Mat frame;
        cap >> frame;
        if (frame.empty()) { 
            std::cerr << "Cam Error (Reconnecting...)" << std::endl; 
            cap.open(camera_url); // Auto-reconnect
            sleep(1);
            continue; 
        }

        cv::Mat gray;
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
        std::vector<cv::Rect> faces;
        face_cascade.detectMultiScale(gray, faces, 1.1, 4);

        double head_yaw = 0;
        double head_velocity = 0; // "Hyperactivity Index"
        double gaze_score = 0; 
        bool is_focused = false;
        double muscle_noise = 0;
        int eyes_found = 0;

        if (faces.size() > 0) {
            total_frames++;
            cv::Rect face = faces[0];
            cv::rectangle(frame, face, cv::Scalar(0, 255, 0), 2);
            int face_cx = face.x + (face.width / 2);
            int frame_cx = frame.cols / 2;
            head_yaw = abs((double)(face_cx - frame_cx));

            // Hyperactivity Index (Velocity)
            head_velocity = abs(head_yaw - last_yaw);
            last_yaw = head_yaw;

            // Eye Tracking
            cv::Mat faceROI = frame(face);
            std::vector<cv::Rect> eyes;
            eye_cascade.detectMultiScale(faceROI, eyes, 1.1, 3);
            
            double total_eye_offset = 0;
            eyes_found = eyes.size();

            for (size_t j = 0; j < eyes.size(); j++) {
                if (eyes[j].y > face.height / 2) continue; 
                cv::Mat eyeROI = faceROI(eyes[j]);
                total_eye_offset += get_eye_gaze_offset(eyeROI);
                cv::rectangle(frame, cv::Point(face.x+eyes[j].x, face.y+eyes[j].y), 
                              cv::Point(face.x+eyes[j].x+eyes[j].width, face.y+eyes[j].y+eyes[j].height), cv::Scalar(255,0,0), 1);
            }
            if (eyes_found > 0) gaze_score = total_eye_offset / eyes_found;
            else gaze_score = 1.0; 

            // BLINK DETECTION (Face yes, Eyes no)
            if (eyes_found == 0) {
                if (!eyes_were_closed) {
                    blink_counter++;
                    eyes_were_closed = true;
                    cv::putText(frame, "BLINK", cv::Point(50,50), cv::FONT_HERSHEY_SIMPLEX, 1, cv::Scalar(0,255,255), 2);
                }
            } else {
                eyes_were_closed = false;
            }

            // FUSION LOGIC
            if (head_yaw < 80 && gaze_score < 0.4) {
                is_focused = true;
                focused_frames++;
            }

            // Muscle Artifacts
            if (head_velocity > 5.0) {
                muscle_noise = (rand() % 8000); 
            }
        } 

        // CALCULATE FOCUS RATIO
        double focus_ratio = (total_frames > 0) ? ((double)focused_frames / total_frames) : 0.0;

        // PHYSICS SIMULATION (8-Band)
        if (is_focused) {
            delta = jitter(15000, 5000); theta = jitter(10000, 3000);
            low_alpha = jitter(8000, 2000); high_alpha = jitter(9000, 2000);
            low_beta = jitter(25000, 5000) + muscle_noise; 
            high_beta = jitter(22000, 5000) + muscle_noise;
            low_gamma = jitter(15000, 4000); mid_gamma = jitter(12000, 3000);
        } else {
            delta = jitter(60000, 10000); theta = jitter(45000, 8000);
            low_alpha = jitter(20000, 5000); high_alpha = jitter(18000, 5000);
            low_beta = jitter(9000, 2000) + muscle_noise; 
            high_beta = jitter(8000, 2000) + muscle_noise;
            low_gamma = jitter(4000, 1000); mid_gamma = jitter(3000, 1000);
        }

        double pn = pink_noise(noise_state);
        theta += pn; low_beta += pn;

        // JSON PACKET (Added: Blink Rate, Hyperactivity, Focus Ratio)
        long long now = current_timestamp();
        char raw_json[1024];
        snprintf(raw_json, sizeof(raw_json), 
            "{\"timestamp\": %lld, "
            "\"eeg_power\": {"
                "\"delta\": %.0f, \"theta\": %.0f, "
                "\"low_alpha\": %.0f, \"high_alpha\": %.0f, "
                "\"low_beta\": %.0f, \"high_beta\": %.0f, "
                "\"low_gamma\": %.0f, \"mid_gamma\": %.0f"
            "}, "
            "\"vision\": {"
                "\"yaw\": %.2f, \"gaze\": %.2f, \"attention\": %.2f, "
                "\"blink_count\": %d, \"hyperactivity_index\": %.2f, \"focus_ratio\": %.2f"
            "}}",
            now, 
            delta, theta, low_alpha, high_alpha, low_beta, high_beta, low_gamma, mid_gamma,
            head_yaw, gaze_score, is_focused ? 1.0 : 0.0, 
            blink_counter, head_velocity, focus_ratio
        );

        unsigned char ciphertext[2048];
        int len = encrypt_aes((unsigned char*)raw_json, strlen(raw_json), MY_AES_KEY, AES_IV, ciphertext);
        char* b64 = base64_encode(ciphertext, len);
        
        char msg[2048];
        snprintf(msg, sizeof(msg), "EEG_SECURE %s", b64);
        zmq_send(publisher, msg, strlen(msg), 0);
        free(b64);

        std::cout << "[SIM] FocusRatio: " << focus_ratio << " | Blink: " << blink_counter << std::endl;
        cv::imshow("NeuroBloom Ultimate", frame);
        cv::waitKey(33);
    }
}