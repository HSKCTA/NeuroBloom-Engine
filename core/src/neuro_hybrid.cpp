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

// --- ROBUST EYE TRACKING (CROPPED) ---
double get_eye_gaze_offset(cv::Mat &eye_roi) {
    if (eye_roi.empty()) return 1.0; 

    cv::Mat gray_eye;
    cv::cvtColor(eye_roi, gray_eye, cv::COLOR_BGR2GRAY);
    
    // CROP TOP 30% (Removes Eyebrows)
    int y_cutoff = eye_roi.rows * 0.30;
    int h_cropped = eye_roi.rows - y_cutoff;
    
    if (h_cropped <= 0 || eye_roi.cols <= 0) return 1.0;

    cv::Rect crop_rect(0, y_cutoff, eye_roi.cols, h_cropped);
    cv::Mat cropped_gray = gray_eye(crop_rect);
    cv::equalizeHist(cropped_gray, cropped_gray); 

    cv::Point minLoc; 
    double minVal;
    cv::minMaxLoc(cropped_gray, &minVal, NULL, &minLoc, NULL);

    // DEBUG: Draw Red Dot on Pupil
    cv::Point pupil_center(minLoc.x, minLoc.y + y_cutoff);
    cv::circle(eye_roi, pupil_center, 4, cv::Scalar(0, 0, 255), -1); 

    double center_x = (double)gray_eye.cols / 2.0;
    double offset = abs(minLoc.x - center_x) / center_x; 
    
    return offset;
}

int main() {
    std::cout << "[SYSTEM] Starting NeuroBloom ADHD Engine (Focus/Distract Only)..." << std::endl;

    void *context = zmq_ctx_new();
    void *publisher = zmq_socket(context, ZMQ_PUB);
    int linger = 0; zmq_setsockopt(publisher, ZMQ_LINGER, &linger, sizeof(linger));
    zmq_bind(publisher, ZMQ_PORT);

    // CAMERA SETUP
    cv::VideoCapture cap(0);
    
    cv::CascadeClassifier face_cascade, eye_cascade;
    if(!face_cascade.load("bridge/haarcascade_frontalface_default.xml")) std::cerr << "No Face XML" << std::endl;
    if(!eye_cascade.load("bridge/haarcascade_eye.xml")) std::cerr << "No Eye XML" << std::endl;

    // STATE VARIABLES
    cv::Rect stable_face = cv::Rect(0,0,0,0); 
    double noise_state = 0;
    
    long total_frames = 0;
    long focused_frames = 0;
    int blink_counter = 0;
    bool eyes_were_closed = false;

    double delta, theta, low_alpha, high_alpha, low_beta, high_beta, low_gamma, mid_gamma;

    while (1) {
        cv::Mat frame;
        cap >> frame;
        if (frame.empty()) { 
            cap.open(0); sleep(1); continue; 
        }

        cv::Mat gray;
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
        std::vector<cv::Rect> faces;
        face_cascade.detectMultiScale(gray, faces, 1.1, 4);

        double head_yaw = 0;
        double gaze_score = 0; 
        bool is_focused = false;
        int eyes_found = 0;

        if (faces.size() > 0) {
            // HYSTERESIS STABILIZER
            if (stable_face.width == 0 || 
                abs(faces[0].x - stable_face.x) > 5 || 
                abs(faces[0].y - stable_face.y) > 5) {
                stable_face = faces[0];
            }

            total_frames++;
            cv::rectangle(frame, stable_face, cv::Scalar(0, 255, 0), 2);
            
            int face_cx = stable_face.x + (stable_face.width / 2);
            int frame_cx = frame.cols / 2;
            head_yaw = abs((double)(face_cx - frame_cx));

            // Eye Tracking
            cv::Mat faceROI = frame(stable_face);
            std::vector<cv::Rect> eyes;
            eye_cascade.detectMultiScale(faceROI, eyes, 1.1, 3);
            
            double total_eye_offset = 0;
            eyes_found = eyes.size();

            for (size_t j = 0; j < eyes.size(); j++) {
                if (eyes[j].y > stable_face.height / 2) continue; 
                cv::Mat eyeROI = faceROI(eyes[j]);
                total_eye_offset += get_eye_gaze_offset(eyeROI);
                cv::rectangle(frame, cv::Point(stable_face.x+eyes[j].x, stable_face.y+eyes[j].y), 
                              cv::Point(stable_face.x+eyes[j].x+eyes[j].width, stable_face.y+eyes[j].y+eyes[j].height), cv::Scalar(255,0,0), 1);
            }
            if (eyes_found > 0) gaze_score = total_eye_offset / eyes_found;
            else gaze_score = 1.0; 

            if (eyes_found == 0) {
                if (!eyes_were_closed) {
                    blink_counter++;
                    eyes_were_closed = true;
                    cv::putText(frame, "BLINK", cv::Point(50,50), cv::FONT_HERSHEY_SIMPLEX, 1, cv::Scalar(0,255,255), 2);
                }
            } else { eyes_were_closed = false; }

            // --- SIMPLIFIED DIAGNOSTIC LOGIC ---
            // If you are looking generally at center (yaw < 80) and eyes are centered (score < 0.5)
            if (head_yaw < 80 && gaze_score < 0.5) {
                is_focused = true;
                focused_frames++;
            }
            // Otherwise, you are DISTRACTED (No "High Stress" option anymore)
        } 

        double focus_ratio = (total_frames > 0) ? ((double)focused_frames / total_frames) : 0.0;

        // DEBUG OVERLAY
        cv::Scalar statusColor = is_focused ? cv::Scalar(0, 255, 0) : cv::Scalar(0, 0, 255);
        std::string statusText = is_focused ? "STATE: FOCUSED" : "STATE: DISTRACTED";
        cv::putText(frame, statusText, cv::Point(20, frame.rows - 20), cv::FONT_HERSHEY_SIMPLEX, 0.8, statusColor, 2);

        // --- PHYSICS SIMULATION (ADHD MODEL) ---
        if (is_focused) {
            // FOCUSED: High Beta (Concentration), Low Theta
            delta = jitter(15000, 5000); 
            theta = jitter(10000, 3000); // Low Theta
            low_alpha = jitter(8000, 2000); 
            high_alpha = jitter(9000, 2000);
            low_beta = jitter(25000, 5000); // High Beta
            high_beta = jitter(18000, 3000); // Reduced from 22000 for less stress-like spikes
            low_gamma = jitter(15000, 4000); 
            mid_gamma = jitter(12000, 3000);
        } else {
            // DISTRACTED: High Theta (Daydreaming), Low Beta
            delta = jitter(20000, 5000); 
            theta = jitter(45000, 8000); // High Theta Spike
            low_alpha = jitter(20000, 5000); 
            high_alpha = jitter(18000, 5000);
            low_beta = jitter(9000, 2000); // Beta Drops
            high_beta = jitter(7000, 1500); // Reduced from 8000
            low_gamma = jitter(4000, 1000); 
            mid_gamma = jitter(3000, 1000);
        }

        double pn = pink_noise(noise_state);
        theta += pn; low_beta += pn;

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
                "\"blink_count\": %d, \"hyperactivity_index\": 0.0, \"focus_ratio\": %.2f"
            "}}",
            now, 
            delta, theta, low_alpha, high_alpha, low_beta, high_beta, low_gamma, mid_gamma,
            head_yaw, gaze_score, is_focused ? 1.0 : 0.0, 
            blink_counter, focus_ratio
        );

        unsigned char ciphertext[2048];
        int len = encrypt_aes((unsigned char*)raw_json, strlen(raw_json), MY_AES_KEY, AES_IV, ciphertext);
        char* b64 = base64_encode(ciphertext, len);
        
        char msg[2048];
        snprintf(msg, sizeof(msg), "EEG_SECURE %s", b64);
        zmq_send(publisher, msg, strlen(msg), 0);
        free(b64);

        std::cout << "[SIM] State: " << (is_focused ? "FOCUSED" : "DISTRACTED") << " | Ratio: " << focus_ratio << std::endl;
        cv::imshow("NeuroBloom ADHD Engine", frame);
        cv::waitKey(33);
    }
}